import { KOLIBRI_CONFIG, MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"
import { ContractOriginationResult, loadContract, printConfig, sendOperation, getTezos, fetchFromCacheOrRun, deployContract, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendTokens } from "@hover-labs/tezos-utils"
import { generateBreakGlassStorage } from '../storage/break-glass-contract-storage'
import { generateQuipuswapProxyStorage } from '../storage/quipuswap-proxy-contract-storage'
import CACHE_KEYS from '../cache-keys'

const main = async () => {
  try {
    // Debug Info
    console.log("Migrating contracts to 1.2.2")
    printConfig(NETWORK_CONFIG)
    console.log('')

    // Init Deployer
    console.log("Initializing Deployer Account")
    const tezos = await getTezos(NETWORK_CONFIG)
    const deployAddress = await tezos.signer.publicKeyHash()
    console.log("Deployer initialized!")
    console.log('')

    // Load Contract Sources
    console.log("Loading Contracts...")
    const contractSources = {
      quipuswapProxyContract: loadContract(`${__dirname}/../../../../smart_contracts/quipuswap-proxy.tz`),
      breakGlassContractSource: loadContract(`${__dirname}/../../../../break-glass-contracts/smart_contracts/break-glass.tz`),
    }
    console.log("Done!")
    console.log('')

    // Step 0: Deploy the Quipuswap proxy
    console.log("Deploying the Quipuswap Proxy")
    const quipuswapProxyDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.QUIPUSWAP_PROXY_DEPLOY, async () => {
      const storage = await generateQuipuswapProxyStorage({
        governorContractAddress: deployAddress,
        harbingerContractAddress: MIGRATION_CONFIG.harbingerNormalizerWithViewsAddress,
        liquidityPoolContractAddress: KOLIBRI_CONFIG.contracts.LIQUIDITY_POOL!,
        maxDataDelaySec: MIGRATION_CONFIG.maxDataDelaySecs,
        pauseGuardianContractAddress: KOLIBRI_CONFIG.contracts.PAUSE_GUARDIAN!,
        quipuswapContractAddress: KOLIBRI_CONFIG.contracts.DEXES.QUIPUSWAP.POOL!,
        slippageTolerance: MIGRATION_CONFIG.slippageTolerance         
      })
      return deployContract(NETWORK_CONFIG, tezos, contractSources.quipuswapProxyContract, storage)
    })
    console.log("")

    // Step 1: Deploy the Quipuswap proxy break glass
    console.log("Deploying the Quipuswap Proxy Break Glass")
    const quipuswapProxyBreakGlassDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.QUIPUSWAP_PROXY_BREAK_GLASS_DEPLOY, async () => {
      const breakGlassStorage = generateBreakGlassStorage(
        {
          daoAddress: KOLIBRI_CONFIG.contracts.DAO!,
          multisigAddress: KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!,
          targetAddress: quipuswapProxyDeployResult.contractAddress

        }
      )
      return deployContract(NETWORK_CONFIG, tezos, contractSources.breakGlassContractSource, breakGlassStorage)
    })
    console.log("")

    // Step 2: Wire break glass
    console.log("Wiring the Break Glass to the Proxy")
    const wireHash = await fetchFromCacheOrRun(CACHE_KEYS.QUIPUSWAP_PROXY_BREAK_GLASS_WIRE, async () => {
      return sendOperation(
        NETWORK_CONFIG,
        tezos,
        quipuswapProxyDeployResult.contractAddress,
        'setGovernorContract',
        quipuswapProxyBreakGlassDeployResult.contractAddress
      )
    })
    console.log("")

    // Print Results
    console.log("----------------------------------------------------------------------------")
    console.log("Operation Results")
    console.log("----------------------------------------------------------------------------")

    console.log("Contracts:")
    console.log(`Quipuswap Proxy:                       ${quipuswapProxyDeployResult.contractAddress} / ${quipuswapProxyDeployResult.operationHash}`)
    console.log(`Quipuswap Proxy Break Glass Contract:  ${quipuswapProxyBreakGlassDeployResult.contractAddress} / ${quipuswapProxyBreakGlassDeployResult.operationHash}`)
    console.log("")

    console.log("Operations:")
    console.log(`Wire Break Glass: ${wireHash}`)
    console.log("")
  } catch (e: any) {
    console.log(e)
  }
}

main()