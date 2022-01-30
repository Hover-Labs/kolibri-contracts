import { KOLIBRI_CONFIG, MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"
import { ContractOriginationResult, loadContract, printConfig, sendOperation, getTezos, fetchFromCacheOrRun, deployContract, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendTokens } from "@hover-labs/tezos-utils"
import { generateBreakGlassStorage } from '../storage/break-glass-contract-storage'
import { generateStabilityFundStorage } from '../storage/stability-fund-contract-storage'
import { generateSavingsPoolStorage } from "../storage/savings-pool-contract-storage"
import { generateMultisigStorage } from '../storage/multisig-storage'
import CACHE_KEYS from '../cache-keys'
import BigNumber from 'bignumber.js'
import { deployAndWireFarmingSystem} from '../deploy-farm'

const main = async () => {
    // Debug Info
    console.log("Deploying a Farm")
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
      farmContract: loadContract(`${__dirname}/../../../../kolibri-farms/smart_contracts/farm-contract.json`),
      reserveContract: loadContract(`${__dirname}/../../../../kolibri-farms/smart_contracts/farm-reward-reserve.tz`),
    }
    console.log("Done!")
    console.log('')

    // Deploy Pipeline

    // Step 0: Deploy a farm
    const result = await fetchFromCacheOrRun(CACHE_KEYS.FARMING_SYSTEM, async () => {
      return deployAndWireFarmingSystem(
        contractSources, 
        MIGRATION_CONFIG.farmingConfig, 
        KOLIBRI_CONFIG.contracts.DAO!, 
        KOLIBRI_CONFIG.contracts.DAO_COMMUNITY_FUND!, 
        KOLIBRI_CONFIG.contracts.DAO_TOKEN!, 
        NETWORK_CONFIG, 
        tezos
      )
    })   
    console.log("")


    console.log(JSON.stringify(result))
    console.log("")

}

main()