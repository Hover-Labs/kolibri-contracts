import { validateBreakGlass, validateStorageValue, fetchFromCache, ContractOriginationResult, getTezos } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { KOLIBRI_CONFIG, NETWORK_CONFIG } from "../config"

const main = async () => {
  console.log("Verifying the Developer Fund Rotation")
  console.log("")

  // Load signer
  const tezos = await getTezos(NETWORK_CONFIG)

  // Load contracts
  const breakGlassMultisigAddress = KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!
  const daoAddress = KOLIBRI_CONFIG.contracts.DAO!
  const minterAddress = KOLIBRI_CONFIG.contracts.MINTER!

  // Load artifacts
  const devFundContractAddress = (await fetchFromCache(CACHE_KEYS.DEV_FUND_DEPLOY) as ContractOriginationResult).contractAddress
  const devFundBreakGlassContractAddress = (await fetchFromCache(CACHE_KEYS.DEV_FUND_BREAK_GLASS_DEPLOY) as ContractOriginationResult).contractAddress

  console.log("Verifying Break Glass")
  await validateBreakGlass(
    devFundContractAddress,
    'governorContractAddress',
    devFundBreakGlassContractAddress,
    breakGlassMultisigAddress,
    daoAddress,
    tezos
  )
  console.log("   / passed")
  console.log("")

  console.log("Verifying Minter is wired correctly")
  await validateStorageValue(minterAddress, 'developerFundContractAddress', devFundContractAddress, tezos)
  console.log("   / passed")
  console.log("")

  console.log("All tests pass!")
}
main()