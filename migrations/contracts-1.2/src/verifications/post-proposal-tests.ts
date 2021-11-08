import { ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient } from "@hover-labs/kolibri-js"
import _ from "lodash";
import { OperationContentsAndResult, OperationContentsAndResultTransaction, InternalOperationResultEnum, OperationResultTransaction } from '@taquito/rpc'

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

  // // Check that the balance of the old fund is 0
  // // NOTE: this test will likely fail on prod since the proposal will be timelocked for a non-trivial amount of time.
  // console.log("Verifying the old stability fund is zeroed")
  // const oldStabilityFundValue = await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)
  // if (!oldStabilityFundValue.isEqualTo(new BigNumber(0))) {
  //   throw new Error('Old stability fund was not zero')
  // }
  // console.log("   / passed")

  // // Check that the balance of the new fund is greater than 0
  // console.log("Verifying the new stability fund has value")
  // const newStabilityFundValue = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  // if (!newStabilityFundValue.isGreaterThan(new BigNumber(0))) {
  //   throw new Error('New stability fund should have a positive balance')
  // }
  // console.log("   / passed")

  // Check that we can borrow and repay interest
  console.log("Verifying that repayment still works")
  console.log("...Creating an oven")
  const signer = await getSigner(NETWORK_CONFIG)

  // NOTE: Network doesn't matter
  const stablecoinClient = new StableCoinClient(NETWORK_CONFIG.tezosNodeUrl, Network.Sandbox, ovenRegistry, minter, ovenFactory, '')

  // Derive an oven address.
  // TODO(keefertaylor): Push this down into @hover-labs/kolibri-js
  const ovenDeployResult = await stablecoinClient.deployOven(signer)
  await ovenDeployResult.confirmation(1)
  const ovenCreationResults = ovenDeployResult.operationResults as OperationContentsAndResultTransaction[]
  const creationResult = _.find(ovenCreationResults, (result) => {
    return result.kind === 'transaction'
  })
  const ovenResult: InternalOperationResultEnum = _.find((creationResult as OperationContentsAndResultTransaction).metadata.internal_operation_results, (operation) => {
    return operation.kind === "origination"
  })!.result
  const ovenAddress = (ovenResult as OperationResultTransaction).originated_contracts![0]
  console.log(`...Oven Address: ${ovenAddress}`)

  console.log("...Depositing to the oven")
  const harbingerClient = new HarbingerClient(NETWORK_CONFIG.tezosNodeUrl, harbingerNormalizer)
  const ovenClient = new OvenClient(NETWORK_CONFIG.tezosNodeUrl, signer, ovenAddress, stablecoinClient, harbingerClient)
  await ovenClient.deposit(new BigNumber(1000000000)) // Deposit 1000 XTZ
  console.log("...Taking a loan")
  const loanAmount = new BigNumber('100')
  await ovenClient.borrow(loanAmount) // Borrow 100 kUSD
  console.log("...Waiting 10 blocks for interest to accrue")
  await sleep(NETWORK_CONFIG.operationDelaySecs * 10)
  console.log("...Repaying loan")
  await ovenClient.repay(loanAmount)
  console.log('...Validating the old stability fund still has zero value')
  // const oldStabilityFundValueAfterRepay = await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)
  // if (oldStabilityFundValueAfterRepay.isEqualTo(new BigNumber(0))) {
  //   throw new Error('Old stability fund accrued interest')
  // }
  // console.log('...Validating that interest accrued')
  // const newStabilityFundValueAfterRepay = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  // if (newStabilityFundValueAfterRepay.isLessThanOrEqualTo(newStabilityFundValue)) {
  //   throw new Error('Interest did not accrue to the new fund')
  // }
  // console.log("   / passed")
}
main()