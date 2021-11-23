import { approveToken, checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient, deriveOvenAddress, SavingsPoolClient } from "@hover-labs/kolibri-js"
import _ from "lodash";
import { TransactionWalletOperation } from '@taquito/taquito'
import { KOLIBRI_CONFIG } from "../config"

const main = async () => {
  console.log("Validating end state is correct")
  console.log("")

  // Load contracts
  const tezos = await getTezos(NETWORK_CONFIG)
  const stabilityFund = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPool = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_DEPLOY) as ContractOriginationResult).contractAddress
  const stabilityFundBreakGlass = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolBreakGlass = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  const minter = KOLIBRI_CONFIG.contracts.MINTER!
  const breakGlassMsig = KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const dao = KOLIBRI_CONFIG.contracts.DAO!
  const oldStabilityFund = KOLIBRI_CONFIG.contracts.STABILITY_FUND!
  const token = KOLIBRI_CONFIG.contracts.TOKEN!
  const ovenRegistry = KOLIBRI_CONFIG.contracts.OVEN_REGISTRY!
  const ovenFactory = KOLIBRI_CONFIG.contracts.OVEN_FACTORY!
  const harbingerNormalizer = KOLIBRI_CONFIG.contracts.HARBINGER_NORMALIZER!

  // Time to wait for interest to accrue.
  const minutesToWait = 5

  // Get a local signer to use with Kolibri-JS
  const signer = await getSigner(NETWORK_CONFIG)
  const deployAddress = await signer.publicKeyHash()

  // Sanity check that the user has funds
  const requiredXTZ = new BigNumber(10 * CONSTANTS.XTZ_MANTISSA)
  const xtzHeld = await tezos.tz.getBalance(deployAddress)
  if (xtzHeld.isLessThan(requiredXTZ)) {
    throw new Error(`${deployAddress} does not have the required XTZ to complete this migration.\nBalance: ${xtzHeld.toFixed()} XTZ\nRequired: ${requiredXTZ.toFixed()} XTZ`)
  }

  console.log(``)
  console.log(`New Stability Fund: ${stabilityFund}`)
  console.log(`Old Stability Fund: ${oldStabilityFund}`)
  console.log(``)

  // Check wiring for savings pool
  console.log("Verifying savings pool break glass is attached to savings pool")
  await validateBreakGlass(savingsPool, 'governorContractAddress', savingsPoolBreakGlass, breakGlassMsig, dao, tezos)
  console.log("   / passed")

  console.log("Verifying savings pool is attached to savings pool break glass")
  await validateStorageValue(savingsPool, 'governorContractAddress', savingsPoolBreakGlass, tezos)
  console.log("   / passed")

  console.log("Verifying savings pool is attached to stability fund")
  await validateStorageValue(savingsPool, 'stabilityFundContractAddress', stabilityFund, tezos)
  console.log("   / passed")

  // Check wiring for stability fund
  console.log("Verifying stability fund break glass is attached to stability fund")
  await validateBreakGlass(stabilityFund, 'governorContractAddress', stabilityFundBreakGlass, breakGlassMsig, dao, tezos)
  console.log("   / passed")

  console.log("Verifying stability fund is attached to stability fund break glass")
  await validateStorageValue(stabilityFund, 'governorContractAddress', stabilityFundBreakGlass, tezos)
  console.log("   / passed")

  console.log("Verifying stability fund is attached to savings pool")
  await validateStorageValue(stabilityFund, 'savingsAccountContractAddress', savingsPool, tezos)
  console.log("   / passed")

  // Check wiring for minter
  console.log("Verifying minter is attached to new stability fund")
  await validateStorageValue(minter, 'stabilityFundContractAddress', stabilityFund, tezos)
  console.log("   / passed")

  // Check that the balance of the old fund is 0
  // NOTE: this test will likely fail on prod since the proposal will be timelocked for a non-trivial amount of time.
  console.log("Verifying the old stability fund is zeroed")
  const oldStabilityFundValue = await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)
  if (!oldStabilityFundValue.isEqualTo(new BigNumber(0))) {
    throw new Error('Old stability fund was not zero')
  }
  console.log("   / passed")

  // Check that the balance of the new fund is greater than 0
  console.log("Verifying the new stability fund has value")
  const newStabilityFundValue = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  if (!newStabilityFundValue.isGreaterThan(new BigNumber(0))) {
    throw new Error('New stability fund should have a positive balance')
  }
  console.log("   / passed")

  // Check that we can borrow and repay interest
  console.log("Verifying that repayment still works")
  console.log("...Creating an oven")

  // NOTE: Network doesn't matter
  const stablecoinClient = new StableCoinClient(NETWORK_CONFIG.tezosNodeUrl, Network.Sandbox, ovenRegistry, minter, ovenFactory, '')

  // Deploy an oven
  const ovenDeployResult: TransactionWalletOperation = (await stablecoinClient.deployOven(signer)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, ovenDeployResult.opHash)
  console.log(`...Operation confirmed in hash ${ovenDeployResult.opHash}`)
  const ovenAddress = await deriveOvenAddress(ovenDeployResult)
  console.log(`...Oven Address: ${ovenAddress}`)

  console.log("...Depositing to the oven")
  const harbingerClient = new HarbingerClient(NETWORK_CONFIG.tezosNodeUrl, harbingerNormalizer)
  const ovenClient = new OvenClient(NETWORK_CONFIG.tezosNodeUrl, signer, ovenAddress, stablecoinClient, harbingerClient)
  const depositResult = (await ovenClient.deposit()) as TransactionWalletOperation // Deposit 1000 XTZ
  await checkConfirmed(NETWORK_CONFIG, depositResult.opHash)

  console.log("...Taking a loan")
  const loanAmount = new BigNumber(100).times(new BigNumber(CONSTANTS.MANTISSA))
  const borrowResult = (await ovenClient.borrow(loanAmount)) as TransactionWalletOperation // Borrow 100 kUSD
  await checkConfirmed(NETWORK_CONFIG, borrowResult.opHash)

  console.log(`...Waiting ${minutesToWait} minutes for interest to accrue (Started at ${(new Date()).toString()}`)
  await sleep(minutesToWait * 60)

  console.log("...Repaying loan")
  const repayResult = (await ovenClient.repay(loanAmount)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, repayResult.opHash)
  console.log(`...Repaid in ${repayResult.opHash} `)

  console.log('...Validating the old stability fund still has zero value')
  const oldStabilityFundValueAfterRepay = await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)
  if (!oldStabilityFundValueAfterRepay.isEqualTo(new BigNumber(0))) {
    throw new Error('Old stability fund accrued interest')
  }
  console.log('...Validating that interest accrued')
  const newStabilityFundValueAfterRepay = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  if (newStabilityFundValueAfterRepay.isLessThanOrEqualTo(newStabilityFundValue)) {
    throw new Error('Interest did not accrue to the new fund')
  }
  console.log("   / passed")
  console.log("")

  // Check that interest can be accrued from the savings pool
  console.log("Verifying users can accrue interest")
  const savingsPoolClient = new SavingsPoolClient(NETWORK_CONFIG.tezosNodeUrl, signer, savingsPool)
  const initialBalance = await getTokenBalanceFromDefaultSmartPyContract(deployAddress, token, tezos)
  const depositAmount = new BigNumber(100).times(new BigNumber(CONSTANTS.MANTISSA))

  console.log("...Zeroing kUSD Approval for Savings Pool")
  await approveToken(savingsPool, new BigNumber(0), token, tezos, NETWORK_CONFIG)

  console.log("...Zeroing LP Token Approval for Savings Pool")
  await approveToken(savingsPool, new BigNumber(0), savingsPool, tezos, NETWORK_CONFIG)

  console.log("...Taking a loan")
  const savingsPoolBorrowResult = (await ovenClient.borrow(loanAmount)) as TransactionWalletOperation // Borrow 100 kUSD
  await checkConfirmed(NETWORK_CONFIG, savingsPoolBorrowResult.opHash)
  console.log(`...Initial kUSD Balance: ${initialBalance.toString()}`)

  console.log(`...Issuing an approval for ${depositAmount.toString()} kUSD to be spent by the pool`)
  await approveToken(savingsPool, depositAmount, token, tezos, NETWORK_CONFIG)

  console.log(`...Depositing ${depositAmount.toString()} to pool`)
  const savingsPoolDepositResult = (await savingsPoolClient.deposit(depositAmount)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, savingsPoolDepositResult.opHash)
  const lpTokenBalance = await getTokenBalanceFromDefaultSmartPyContract(deployAddress, savingsPool, tezos)
  console.log(`...Deposit completed in hash ${savingsPoolDepositResult.opHash}`)
  console.log(`...Received ${lpTokenBalance} LP tokens`)

  console.log(`...Waiting ${minutesToWait} minutes for interest to accrue (Started at ${(new Date()).toString()}`)
  await sleep(minutesToWait * 60)

  console.log(`...Approving ${lpTokenBalance.toString()} LP tokens to be spent by the pool`)
  await approveToken(savingsPool, lpTokenBalance, savingsPool, tezos, NETWORK_CONFIG)

  console.log(`...Redeeming ${lpTokenBalance.toString()} against the pool`)
  const savingPoolRedeemResult = (await savingsPoolClient.redeem(lpTokenBalance)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, savingPoolRedeemResult.opHash)
  console.log(`...Redeem completed in hash ${savingPoolRedeemResult.opHash}`)

  console.log("...Validating the pool has 0 kUSD")
  const savingsPoolkUSDBalance = await getTokenBalanceFromDefaultSmartPyContract(savingsPool, token, tezos)
  if (!savingsPoolkUSDBalance.isEqualTo(0)) {
    throw new Error("The savings pool contained value after it should be empty")
  }
  console.log("   / passed")

  console.log("...Validating there are 0 LP tokens issued")
  const savingsPoolContract = await tezos.contract.at(savingsPool)
  const savingsPoolStorage: any = await savingsPoolContract.storage()
  if (!savingsPoolStorage.totalSupply.isEqualTo(0)) {
    throw new Error("The savings pool contained value after it should be empty")
  }
  console.log("   / passed")

  console.log("...Validating the user received interest")
  const balanceAfterRedeem = await getTokenBalanceFromDefaultSmartPyContract(deployAddress, token, tezos)
  if (!balanceAfterRedeem.isGreaterThan(initialBalance)) {
    throw new Error("Balance after redemption did not increase!")
  }
  console.log("   / passed")

  console.log("...Repaying loan")
  const savingsPoolRepayResult = (await ovenClient.repay(loanAmount)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, savingsPoolRepayResult.opHash)
  console.log(`...Repaid in ${savingsPoolRepayResult.opHash} `)

  console.log("")
  console.log("All Tests Pass!")
  console.log(`Note: ${ovenAddress} has ${depositAmount.toString()} mutez in it. We cannot automatically withdraw.`)
}
main()