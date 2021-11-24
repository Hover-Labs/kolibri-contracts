import { validateBreakGlass, validateStorageValue, validateMetadata, fetchFromCache, ContractOriginationResult, getTezos, getStorageValue, validateTokenMetadata } from "@hover-labs/tezos-utils";
import CACHE_KEYS from '../cache-keys'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"

const main = async () => {
  console.log("Validating contract storage")
  console.log("")

  const tezos = await getTezos(NETWORK_CONFIG)

  // Name old / existing artifacts for convenience
  const oldStabilityFundAddress = KOLIBRI_CONFIG.contracts.STABILITY_FUND!
  const breakGlassMultisigAddress = KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const daoAddress = KOLIBRI_CONFIG.contracts.DAO!
  const tokenAddress = KOLIBRI_CONFIG.contracts.TOKEN!

  // Load new artifacts
  const stabilityFundContractAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolContractAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_DEPLOY) as ContractOriginationResult).contractAddress

  const stabilityFundBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress
  const savingsPoolBreakGlassAddress = (await fetchFromCache(CACHE_KEYS.SAVINGS_POOL_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  const stabilityFundGovernorMultisigAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_MSIG) as ContractOriginationResult).contractAddress

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
  // 7. Pause guardian should be the pause guardian.
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

  await validateStorageValue(savingsPoolContractAddress, 'pauseGuardianContractAddress', KOLIBRI_CONFIG.contracts.PAUSE_GUARDIAN, tezos)

  console.log("   / passed")

  // Validate the multisig configuration
  // 1. operationId should start at 0
  // 2. threshold, signers and timelockSeconds shoudl match the MIGRATION_CONFIG
  console.log(`Validating multisig configuration... (${stabilityFundGovernorMultisigAddress})`)

  await validateStorageValue(stabilityFundGovernorMultisigAddress, 'operationId', 0, tezos)

  await validateStorageValue(stabilityFundGovernorMultisigAddress, 'threshold', MIGRATION_CONFIG.stabilityFundMsig.threshold, tezos)
  await validateStorageValue(stabilityFundGovernorMultisigAddress, 'signers', MIGRATION_CONFIG.stabilityFundMsig.publicKeys, tezos)
  await validateStorageValue(stabilityFundGovernorMultisigAddress, 'timelockSeconds', MIGRATION_CONFIG.stabilityFundMsig.timelockSeconds, tezos)
  console.log("   / passed")
  console.log("")

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
  console.log("")
  await validateMetadata(savingsPoolContractAddress, tezos)
  console.log("")
  await validateTokenMetadata(savingsPoolContractAddress, tezos)
  console.log("")
  console.log("   / passed")
  console.log("")

  console.log("All tests passed!")
  console.log("")
}
main()