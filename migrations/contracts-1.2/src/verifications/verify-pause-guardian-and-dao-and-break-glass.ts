import {
  verifyDAOIntegrationWithBreakGlass,
  getTezos, fetchFromCache,
  ContractOriginationResult,
  verifyBreakGlassIntegration,
  callThroughMultisig,
  validateStorageValue,
  pauseContractAndVerify,
} from "@hover-labs/tezos-utils";
import CACHE_KEYS from '../cache-keys'
import { NETWORK_CONFIG } from "../config"


const main = async () => {
  console.log("Validating DAO and Break Glass Integrations")
  console.log("")

  const tezos = await getTezos(NETWORK_CONFIG)

  // Name old / existing artifacts for convenience
  const daoAddress = NETWORK_CONFIG.contracts.DAO!
  const vestingVault = NETWORK_CONFIG.contracts.VESTING_CONTRACTS[(await tezos.signer.publicKeyHash())]!
  const breakGlassMultisigAddress = NETWORK_CONFIG.contracts.BREAK_GLASS_MULTISIG!

  // Load new artifacts
  const stabilityFundContractAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolContractAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_DEPLOY) as ContractOriginationResult).contractAddress

  const stabilityFundBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  console.log("Testing Pause Guardian can pause the contract")
  await pauseContractAndVerify(NETWORK_CONFIG, savingsPoolContractAddress, tezos)
  console.log("   / Passed")
  console.log("")

  console.log("Testing a DAO proposal to unpause the pool")
  await verifyDAOIntegrationWithBreakGlass(
    vestingVault,
    savingsPoolBreakGlassAddress,
    savingsPoolContractAddress,
    'unpause',
    'sp.unit',
    'sp.TUnit',
    daoAddress,
    'paused',
    false,
    tezos,
    NETWORK_CONFIG
  )
  console.log("   / Passed")
  console.log("")

  // NOTE: Since we mess with savings pool storage in this call, this should come after any savings
  //       pool validations. 
  console.log("Testing a DAO Proposal to set the savings contract to the signer")
  await verifyDAOIntegrationWithBreakGlass(
    vestingVault,
    stabilityFundBreakGlassAddress,
    stabilityFundContractAddress,
    'setSavingsAccountContract',
    `sp.address('${await tezos.signer.publicKeyHash()}')`,
    'sp.TAddress',
    daoAddress,
    'savingsAccountContractAddress',
    await tezos.signer.publicKeyHash(),
    tezos,
    NETWORK_CONFIG
  )
  console.log("   / Passed")
  console.log("")

  // Break glasses must go last, otherwise governance calls above will fail

  console.log("Testing break glass can control Stability fund")
  await verifyBreakGlassIntegration(
    stabilityFundBreakGlassAddress,
    stabilityFundContractAddress,
    breakGlassMultisigAddress,
    await tezos.signer.publicKeyHash(),
    tezos,
    NETWORK_CONFIG,
  )
  console.log("   / Passed")
  console.log("")

  console.log("Testing break glass can control Stability fund")
  await verifyBreakGlassIntegration(
    savingsPoolBreakGlassAddress,
    savingsPoolContractAddress,
    breakGlassMultisigAddress,
    await tezos.signer.publicKeyHash(),
    tezos,
    NETWORK_CONFIG,
  )
  console.log("   / Passed")
  console.log("")

  console.log("All tests passed.")
  console.log("")
}
main()