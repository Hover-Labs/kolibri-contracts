import { approveToken, checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendOperation } from "@hover-labs/tezos-utils"
import { NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient, deriveOvenAddress, SavingsPoolClient } from "@hover-labs/kolibri-js"
import _ from "lodash";
import { TransactionWalletOperation } from '@taquito/taquito'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from "../config"

const main = async () => {
  console.log("Validating end state is correct")
  console.log("")

  // Load contracts
  const tezos = await getTezos(NETWORK_CONFIG)
  const liquidityPool = KOLIBRI_CONFIG.contracts.LIQUIDITY_POOL!
  const minter = KOLIBRI_CONFIG.contracts.MINTER!
  const breakGlassMsig = KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const dao = KOLIBRI_CONFIG.contracts.DAO!
  const oldStabilityFund = KOLIBRI_CONFIG.contracts.STABILITY_FUND!
  const token = KOLIBRI_CONFIG.contracts.TOKEN!
  const ovenRegistry = KOLIBRI_CONFIG.contracts.OVEN_REGISTRY!
  const ovenFactory = KOLIBRI_CONFIG.contracts.OVEN_FACTORY!
  const harbingerNormalizer = KOLIBRI_CONFIG.contracts.HARBINGER_NORMALIZER!

  // Get a local signer to use with Kolibri-JS
  const signer = await getSigner(NETWORK_CONFIG)
  const deployAddress = await signer.publicKeyHash()

  // Sanity check that the user has funds
  console.log("Performing Pre Flight Checks...")
  const requiredXTZ = new BigNumber(10 * CONSTANTS.XTZ_MANTISSA)
  const xtzHeld = await tezos.tz.getBalance(deployAddress)
  if (xtzHeld.isLessThan(requiredXTZ)) {
    throw new Error(`${deployAddress} does not have the required XTZ to complete this migration.\nBalance: ${xtzHeld.toFixed()} XTZ\nRequired: ${requiredXTZ.toFixed()} XTZ`)
  }
  console.log("Done!")
  console.log("")

  // Check that address is now null address
  console.log("Verifying that quipuswap address is nulled")
  await validateStorageValue(liquidityPool, 'quipuswapAddress', MIGRATION_CONFIG.nullAddress, tezos)
  console.log("   / passed")

  // Check that we can deposit and withdraw
  console.log("Verifying that we can still deposit to the pool")
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
  const depositResult = (await ovenClient.deposit(requiredXTZ)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, depositResult.opHash)

  console.log("...Taking a loan")
  const loanAmount = new BigNumber(5).times(new BigNumber(CONSTANTS.MANTISSA))
  const borrowResult = (await ovenClient.borrow(loanAmount)) as TransactionWalletOperation // Borrow 5 kUSD
  await checkConfirmed(NETWORK_CONFIG, borrowResult.opHash)

  console.log("...Zeroing allowance for kUSD")
  await approveToken(liquidityPool, new BigNumber(0), token, tezos, NETWORK_CONFIG)

  console.log("...Zeroing allowance for QLkUSD")
  await approveToken(liquidityPool, new BigNumber(0), liquidityPool, tezos, NETWORK_CONFIG)

  console.log("...Approving pool to spend kUSD")
  await approveToken(liquidityPool, loanAmount, token, tezos, NETWORK_CONFIG)

  console.log("...Depositing to pool")
  const depositHash = await sendOperation(NETWORK_CONFIG, tezos, liquidityPool, 'deposit', loanAmount.toFixed())
  await checkConfirmed(NETWORK_CONFIG, depositHash!)

  console.log("...Fetching amount of QLkUSD minted")
  const QLkUSDHeld = await getTokenBalanceFromDefaultSmartPyContract(deployAddress, liquidityPool, tezos)
  console.log(`...Now holding ${QLkUSDHeld.toFixed()} QLkUSD`)
  if (QLkUSDHeld.isEqualTo(0)) {
    throw new Error("Should have QLkUSD")
  }

  console.log("...Approving pool to spend QLkUSD")
  await approveToken(liquidityPool, QLkUSDHeld, liquidityPool, tezos, NETWORK_CONFIG)

  console.log("...Withdrawing kUSD")
  const redeemHash = await sendOperation(NETWORK_CONFIG, tezos, liquidityPool, 'redeem', QLkUSDHeld.toFixed())
  await checkConfirmed(NETWORK_CONFIG, redeemHash!)

  console.log("...Re fetching token balances")
  const QLkUSDHeldAfterRedeem = await getTokenBalanceFromDefaultSmartPyContract(deployAddress, liquidityPool, tezos)
  console.log(`...Holding ${QLkUSDHeldAfterRedeem.toFixed()} QLkUSD`)
  if (!QLkUSDHeldAfterRedeem.isEqualTo(0)) {
    throw new Error("Should have burned all QLkUSD")
  }

  console.log("...Repaying loan")
  const savingsPoolRepayResult = (await ovenClient.repay(loanAmount)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, savingsPoolRepayResult.opHash)
  console.log(`...Repaid in ${savingsPoolRepayResult.opHash} `)

  console.log("")
  console.log("All Tests Pass!")
  console.log(`Note: ${ovenAddress} has ${requiredXTZ.toString()} mutez in it. We cannot automatically withdraw.`)
}
main()