import { validateBreakGlass, validateStorageValue, validateMetadata, fetchFromCache, ContractOriginationResult, getTezos, getStorageValue } from "@hover-labs/tezos-utils";
import CACHE_KEYS from '../cache-keys'
import { MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"

const main = async () => {
  console.log("Validating contract storage")
  console.log("")

  const tezos = await getTezos(NETWORK_CONFIG)

  // Name old / existing artifacts for convenience
  const oldStabilityFundAddress = NETWORK_CONFIG.contracts.STABILITY_FUND!
  const breakGlassMultisigAddress = NETWORK_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const daoAddress = NETWORK_CONFIG.contracts.DAO!
  const tokenAddress = NETWORK_CONFIG.contracts.TOKEN!

  // Load new artifacts
  const stabilityFundContractAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolContractAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_DEPLOY) as ContractOriginationResult).contractAddress

  const stabilityFundBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  // Validate storage for stability fund.
  // 1. governor should be break glass
  // 2. savings account should be the new savings account
  // 3. other fields should be equal
  console.log(`Validating new stability fund storage... (${stabilityFundContractAddress})`)
  await validateStorageValue(stabilityFundContractAddress, 'governorContractAddress', stabilityFundBreakGlassAddress, tezos)

  await validateStorageValue(stabilityFundContractAddress, 'savingsAccountContractAddress', savingsPoolContractAddress, tezos)

  await validateStorageValue(
    stabilityFundContractAddress,
    'administratorContractAddress',
    await getStorageValue(oldStabilityFundAddress, 'administratorContractAddress', tezos),
    tezos
  )
  await validateStorageValue(
    stabilityFundContractAddress,
    'ovenRegistryContractAddress',
    await getStorageValue(oldStabilityFundAddress, 'ovenRegistryContractAddress', tezos),
    tezos
  )
  await validateStorageValue(
    stabilityFundContractAddress,
    'tokenContractAddress',
    await getStorageValue(oldStabilityFundAddress, 'tokenContractAddress', tezos),
    tezos
  )
  console.log("   / passed")

  // Validate storage for savings pool.
  // 1. Governor should be break glass
  // 2. Stability fund should be new stability fund
  // 3. Interest rate should match migration config.
  // 4. Token address should be the same as in the stability fund and the old contract
  // 5. Underlying balance and last interest update time are set to zero
  // 6. Saved states should be set to none, with state = 0 (IDLE)
  console.log(`Validating new savings pool storage... (${savingsPoolContractAddress})`)
  await validateStorageValue(savingsPoolContractAddress, 'governorContractAddress', savingsPoolBreakGlassAddress, tezos)

  await validateStorageValue(savingsPoolContractAddress, 'stabilityFundContractAddress', stabilityFundContractAddress, tezos)

  await validateStorageValue(savingsPoolContractAddress, 'interestRate', MIGRATION_CONFIG.initialInterestRate, tezos)

  await validateStorageValue(
    savingsPoolContractAddress,
    'tokenContractAddress',
    await getStorageValue(oldStabilityFundAddress, 'tokenContractAddress', tezos),
    tezos
  )
  await validateStorageValue(savingsPoolContractAddress, 'tokenContractAddress', tokenAddress, tezos)

  await validateStorageValue(savingsPoolContractAddress, 'lastInterestCompoundTime', new Date(0), tezos)
  await validateStorageValue(savingsPoolContractAddress, 'underlyingBalance', 0, tezos)

  await validateStorageValue(savingsPoolContractAddress, 'state', 0, tezos)
  await validateStorageValue(savingsPoolContractAddress, 'savedState_tokensToRedeem', null, tezos)
  await validateStorageValue(savingsPoolContractAddress, 'savedState_redeemer', null, tezos)
  await validateStorageValue(savingsPoolContractAddress, 'savedState_tokensToDeposit', null, tezos)
  await validateStorageValue(savingsPoolContractAddress, 'savedState_depositor', null, tezos)

  console.log("   / passed")

  // Validate break glasses are attached correctly

  console.log(`Validating break glass for stability fund... (${stabilityFundBreakGlassAddress})`)
  await validateBreakGlass(
    stabilityFundContractAddress,
    'governorContractAddress',
    stabilityFundBreakGlassAddress,
    breakGlassMultisigAddress,
    daoAddress,
    tezos
  )
  console.log("   / passed")

  console.log(`Validating break glass for savings pool... (${savingsPoolBreakGlassAddress})`)
  await validateBreakGlass(
    savingsPoolContractAddress,
    'governorContractAddress',
    savingsPoolBreakGlassAddress,
    breakGlassMultisigAddress,
    daoAddress,
    tezos
  )
  console.log("   / passed")

  console.log("")

  // Validate Metadata
  console.log(`Validating Metadata on Savings Pool... `)
  await validateMetadata(savingsPoolContractAddress, tezos)
  console.log("   / passed")
  console.log("")

  console.log("All tests passed!")
  console.log("")
}
main()