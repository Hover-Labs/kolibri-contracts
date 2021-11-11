import { checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient } from "@hover-labs/kolibri-js"
import _ from "lodash";
import { OperationContentsAndResult, OperationContentsAndResultTransaction, InternalOperationResultEnum, OperationResultTransaction, } from '@taquito/rpc'
import { InMemorySigner } from '@taquito/signer'
import { TransactionWalletOperation } from '@taquito/taquito'

const main = async () => {
  console.log("Validating end state is correct")
  console.log("")

  // Load contracts
  const tezos = await getTezos(NETWORK_CONFIG)
  const stabilityFund = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPool = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_DEPLOY) as ContractOriginationResult).contractAddress
  const stabilityFundBreakGlass = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolBreakGlass = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  const minter = NETWORK_CONFIG.contracts.MINTER!
  const breakGlassMsig = NETWORK_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const dao = NETWORK_CONFIG.contracts.DAO!
  const oldStabilityFund = NETWORK_CONFIG.contracts.STABILITY_FUND!
  const token = NETWORK_CONFIG.contracts.TOKEN!
  const ovenRegistry = NETWORK_CONFIG.contracts.OVEN_REGISTRY!
  const ovenFactory = NETWORK_CONFIG.contracts.OVEN_FACTORY!
  const harbingerNormalizer = NETWORK_CONFIG.contracts.HARBINGER_NORMALIZER!

  console.log(``)
  console.log(`New Stability Fund: ${stabilityFund}`)
  console.log(`Old Stability Fund: ${oldStabilityFund}`)
  console.log(``)

  // Check wiring for savings pool
  // console.log("Verifying savings pool break glass is attached to savings pool")
  // await validateBreakGlass(savingsPool, 'governorContractAddress', savingsPoolBreakGlass, breakGlassMsig, dao, tezos)
  // console.log("   / passed")

  // console.log("Verifying savings pool is attached to savings pool break glass")
  // await validateStorageValue(savingsPool, 'governorContractAddress', savingsPoolBreakGlass, tezos)
  // console.log("   / passed")

  // console.log("Verifying savings pool is attached to stability fund")
  // await validateStorageValue(savingsPool, 'stabilityFundContractAddress', stabilityFund, tezos)
  // console.log("   / passed")

  // // Check wiring for stability fund
  // console.log("Verifying stability fund break glass is attached to stability fund")
  // await validateBreakGlass(stabilityFund, 'governorContractAddress', stabilityFundBreakGlass, breakGlassMsig, dao, tezos)
  // console.log("   / passed")

  // console.log("Verifying stability fund is attached to stability fund break glass")
  // await validateStorageValue(stabilityFund, 'governorContractAddress', stabilityFundBreakGlass, tezos)
  // console.log("   / passed")

  // console.log("Verifying stability fund is attached to savings pool")
  // await validateStorageValue(stabilityFund, 'savingsAccountContractAddress', savingsPool, tezos)
  // console.log("   / passed")

  // // Check wiring for minter
  // console.log("Verifying minter is attached to new stability fund")
  // await validateStorageValue(minter, 'stabilityFundContractAddress', stabilityFund, tezos)
  // console.log("   / passed")

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
  const signer = await getSigner(NETWORK_CONFIG)

  // NOTE: Network doesn't matter
  const stablecoinClient = new StableCoinClient(NETWORK_CONFIG.tezosNodeUrl, Network.Sandbox, ovenRegistry, minter, ovenFactory, '')

  // Deploy an oven
  const ovenDeployResult: TransactionWalletOperation = (await stablecoinClient.deployOven(signer)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, ovenDeployResult.opHash)
  console.log(`...Operation confirmed in hash ${ovenDeployResult.opHash}`)

  // Derive an oven address
  // TODO(keefertaylor): Push this down into @hover-labs/kolibri-js or @hover-labs/tezos-util
  const ovenCreationResults: OperationContentsAndResult[] = await ovenDeployResult.operationResults()
  const transactionResult: OperationContentsAndResultTransaction = _.find(ovenCreationResults, (result) => {
    return result.kind === 'transaction'
  }) as OperationContentsAndResultTransaction
  const ovenResult: InternalOperationResultEnum = _.find(transactionResult.metadata.internal_operation_results, (operation) => {
    return operation.kind === "origination"
  })!.result
  const ovenAddress = (ovenResult as OperationResultTransaction).originated_contracts![0]
  console.log(`...Oven Address: ${ovenAddress}`)

  console.log("...Depositing to the oven")
  const harbingerClient = new HarbingerClient(NETWORK_CONFIG.tezosNodeUrl, harbingerNormalizer)
  const ovenClient = new OvenClient(NETWORK_CONFIG.tezosNodeUrl, signer, ovenAddress, stablecoinClient, harbingerClient)
  const depositResult = (await ovenClient.deposit(new BigNumber(1000 * CONSTANTS.XTZ_MANTISSA))) as TransactionWalletOperation // Deposit 1000 XTZ
  await checkConfirmed(NETWORK_CONFIG, depositResult.opHash)

  console.log("...Taking a loan")
  const loanAmount = new BigNumber(100).times(new BigNumber(CONSTANTS.MANTISSA))
  const borrowResult = (await ovenClient.borrow(loanAmount)) as TransactionWalletOperation // Borrow 100 kUSD
  await checkConfirmed(NETWORK_CONFIG, borrowResult.opHash)

  const minutesToWait = 5
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
}
main()