import { verifyDAOIntegrationWithBreakGlass, getTezos, fetchFromCache, ContractOriginationResult, verifyBreakGlassIntegration } from "@hover-labs/tezos-utils";
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

  console.log("Testing a DAO proposal to set the savings account on the stability pool to signer.")
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

  console.log("Testing a DAO proposal to set the interest rate of stability pool to zero.")
  await verifyDAOIntegrationWithBreakGlass(
    vestingVault,
    savingsPoolBreakGlassAddress,
    savingsPoolContractAddress,
    'setInterestRate',
    'sp.nat(0)',
    'sp.TNat',
    daoAddress,
    'interestRate',
    0,
    tezos,
    NETWORK_CONFIG
  )
  console.log("   / Passed")
  console.log("")

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