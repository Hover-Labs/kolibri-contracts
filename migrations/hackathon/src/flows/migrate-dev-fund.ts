import { KOLIBRI_CONFIG, MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"
import { ContractOriginationResult, loadContract, printConfig, sendOperation, getTezos, fetchFromCacheOrRun, deployContract, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendTokens } from "@hover-labs/tezos-utils"
import { generateBreakGlassStorage } from '../storage/break-glass-storage'
import { generateDevFundStorage } from '../storage/dev-fund-storage'
import CACHE_KEYS from '../cache-keys'

const main = async () => {
  try {
    // Debug Info
    console.log("Migrating dev fund")
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
      devFundContractSource: loadContract(`${__dirname}/../../../../smart_contracts/dev-fund.tz`),
      breakGlassContractSource: loadContract(`${__dirname}/../../../../break-glass-contracts/smart_contracts/break-glass.tz`),
    }
    console.log("Done!")
    console.log('')

    // Deploy Pipeline

    // Step 0: Deploy a new Developer Fund
    console.log("Deploying a new Developer Fund")
    const devFundDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.DEV_FUND_DEPLOY, async () => {
      const params = {
        administratorAddress: KOLIBRI_CONFIG.contracts.PAUSE_GUARDIAN!,
        tokenAddress: KOLIBRI_CONFIG.contracts.TOKEN!,
        governorAddress: deployAddress
      }
      const devFundStorage = generateDevFundStorage(params)
      return deployContract(NETWORK_CONFIG, tezos, contractSources.devFundContractSource, devFundStorage)
    })
    console.log("")

    // Step 1: Deploy a Break Glass
    console.log("Deploying a new Developer Fund Break Glass")
    const devFundBreakGlassDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.DEV_FUND_BREAK_GLASS_DEPLOY, async () => {
      const breakGlassStorage = generateBreakGlassStorage(
        {
          daoAddress: KOLIBRI_CONFIG.contracts.DAO!,
          multisigAddress: KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!,
          targetAddress: devFundDeployResult.contractAddress
        }
      )
      return deployContract(NETWORK_CONFIG, tezos, contractSources.breakGlassContractSource, breakGlassStorage)
    })

    // Step 2: Wire together
    console.log("Wiring Dev Fund Break Glass")
    const wireHash: string = await fetchFromCacheOrRun(CACHE_KEYS.DEV_FUND_BREAK_GLASS_WIRE, async () => {
      return sendOperation(
        NETWORK_CONFIG,
        tezos,
        devFundDeployResult.contractAddress,
        'setGovernorContract',
        devFundBreakGlassDeployResult.contractAddress
      )
    })

    // Print Results
    console.log("----------------------------------------------------------------------------")
    console.log("Operation Results")
    console.log("----------------------------------------------------------------------------")

    console.log("Contracts:")
    console.log(`New Developer Fund Contract:              ${devFundDeployResult.contractAddress} / ${devFundDeployResult.operationHash}`)
    console.log(`New Developer Fund Break Glass Contract:  ${devFundBreakGlassDeployResult.contractAddress} / ${devFundBreakGlassDeployResult.operationHash}`)
    console.log("")

    console.log("Operations:")
    console.log(`Wire Break Glass To Dev Pool: ${wireHash}`)

    console.log("")
  } catch (e: any) {
    console.log(e)
  }
}

main()