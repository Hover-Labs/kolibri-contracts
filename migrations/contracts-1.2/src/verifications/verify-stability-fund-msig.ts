import { checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendTokens, callThroughMultisig } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient, deriveOvenAddress } from "@hover-labs/kolibri-js"
import { TransactionWalletOperation } from '@taquito/taquito'
import { KOLIBRI_CONFIG } from "../config"

const main = async () => {
  console.log("Validating end state is correct")
  console.log("")

  // Load contracts
  const tezos = await getTezos(NETWORK_CONFIG)
  const stabilityFund = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const stabilityFundGovernorMultisigAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_MSIG) as ContractOriginationResult).contractAddress

  const minter = KOLIBRI_CONFIG.contracts.MINTER!
  const oldStabilityFund = KOLIBRI_CONFIG.contracts.STABILITY_FUND!
  const token = KOLIBRI_CONFIG.contracts.TOKEN!
  const ovenRegistry = KOLIBRI_CONFIG.contracts.OVEN_REGISTRY!
  const ovenFactory = KOLIBRI_CONFIG.contracts.OVEN_FACTORY!
  const harbingerNormalizer = KOLIBRI_CONFIG.contracts.HARBINGER_NORMALIZER!

  // Get a local signer to use with Kolibri-JS
  const signer = await getSigner(NETWORK_CONFIG)

  console.log(``)
  console.log(`New Stability Fund: ${stabilityFund}`)
  console.log(`Old Stability Fund: ${oldStabilityFund}`)
  console.log(``)

  // Verify the multisig can move funds
  console.log("Validating that the multisig can move funds from the old stability fund")

  // NOTE: Network doesn't matter
  const stablecoinClient = new StableCoinClient(NETWORK_CONFIG.tezosNodeUrl, Network.Sandbox, ovenRegistry, minter, ovenFactory, '')

  const ovenDeployResult: TransactionWalletOperation = (await stablecoinClient.deployOven(signer)) as TransactionWalletOperation
  await checkConfirmed(NETWORK_CONFIG, ovenDeployResult.opHash)
  console.log(`...Operation confirmed in hash ${ovenDeployResult.opHash}`)
  const ovenAddress = await deriveOvenAddress(ovenDeployResult)
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

  console.log("...Sending some value to the stability fund")
  const kUSDInOldFund = new BigNumber(123456789) // 0.000000000123456789 kUSD
  const sendTokensHash = sendTokens(oldStabilityFund, kUSDInOldFund, token, tezos, NETWORK_CONFIG)
  await checkConfirmed(NETWORK_CONFIG, sendTokensHash)

  console.log("...Validating that value transferred")
  if (!(await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)).isEqualTo(kUSDInOldFund)) {
    throw new Error("The old stability fund did not receive any value!")
  }

  console.log("...Fetching new stability fund's current value")
  const newFundValue = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  console.log(`...New stability fund has ${newFundValue.toFixed()} kUSD in value`)

  console.log("...Moving funds via the multisig")
  await callThroughMultisig(
    NETWORK_CONFIG,
    stabilityFundGovernorMultisigAddress,
    oldStabilityFund,
    'sendTokens',
    `sp.pair(sp.nat(${kUSDInOldFund.toFixed()}), sp.address("${stabilityFund}""))`,
    tezos
  )

  console.log("...Validating that the old stability fund has zero kUSD")
  if (!(await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFund, token, tezos)).isEqualTo(0)) {
    throw new Error("The old stability fund is not zero'ed!")
  }

  console.log("...Validating that the new stability fund received funds")
  const expectedValueInStabilityFund = newFundValue.plus(kUSDInOldFund)
  const actualValueInStabilityFund = await getTokenBalanceFromDefaultSmartPyContract(stabilityFund, token, tezos)
  if (!actualValueInStabilityFund.isEqualTo(expectedValueInStabilityFund)) {
    throw new Error(`New stability fund doesn't have the right value!\nActual: ${actualValueInStabilityFund}\nExpected" ${expectedValueInStabilityFund}`)
  }

  console.log("   / passed")
  console.log("")

  console.log("All Tests Passed!")
  console.log("")
}

main()