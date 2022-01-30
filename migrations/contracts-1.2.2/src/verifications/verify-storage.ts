import { validateBreakGlass, validateStorageValue, validateMetadata, fetchFromCache, ContractOriginationResult, getTezos, getStorageValue, validateTokenMetadata } from "@hover-labs/tezos-utils";
import CACHE_KEYS from '../cache-keys'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"

const main = async () => {
  console.log("Validating contract storage")
  console.log("")

  const tezos = await getTezos(NETWORK_CONFIG)

  // Name old / existing artifacts for convenience
  const liquidityPoolContract = KOLIBRI_CONFIG.contracts.LIQUIDITY_POOL!
  const breakGlassMsig = KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const dao = KOLIBRI_CONFIG.contracts.DAO!
  const pauseGuardian = KOLIBRI_CONFIG.contracts.PAUSE_GUARDIAN!
  const quipuswap = KOLIBRI_CONFIG.contracts.DEXES.QUIPUSWAP.POOL!

  // Load new artifacts
  const quipuswapProxy = (await fetchFromCache(CACHE_KEYS.QUIPUSWAP_PROXY_DEPLOY) as ContractOriginationResult).contractAddress
  const quipuswapProxyBreakGlass = (await fetchFromCache(CACHE_KEYS.QUIPUSWAP_PROXY_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  // Validate break glass
  console.log("Validating Quipuswap Proxy Break Glass")
  await validateBreakGlass(quipuswapProxy, 'governorContractAddress', quipuswapProxyBreakGlass, breakGlassMsig, dao, tezos)
  console.log("    / passed")
  console.log("")

  // Validate quipuswap proxy
  console.log("Validating Quipuswap Proxy storage")
  console.log("   / passed")
  await validateStorageValue(quipuswapProxy, 'harbingerContractAddress', MIGRATION_CONFIG.harbingerNormalizerWithViewsAddress, tezos)
  await validateStorageValue(quipuswapProxy, 'liquidityPoolContractAddress', liquidityPoolContract, tezos)
  await validateStorageValue(quipuswapProxy, 'pauseGuardianContractAddress', pauseGuardian, tezos)
  await validateStorageValue(quipuswapProxy, 'quipuswapContractAddress', quipuswap, tezos)
  await validateStorageValue(quipuswapProxy, 'paused', false, tezos)
  await validateStorageValue(quipuswapProxy, 'maxDataDelaySec', MIGRATION_CONFIG.maxDataDelaySecs, tezos)
  await validateStorageValue(quipuswapProxy, 'slippageTolerance', MIGRATION_CONFIG.slippageTolerance, tezos)  
  console.log("")

  console.log("All tests passed!")
  console.log("")
}
main()