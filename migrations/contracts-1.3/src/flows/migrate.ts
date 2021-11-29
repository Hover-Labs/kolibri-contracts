import { KOLIBRI_CONFIG, NETWORK_CONFIG } from "../config"
import { ContractOriginationResult, loadContract, printConfig, sendOperation, getTezos, fetchFromCacheOrRun, deployContract, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendTokens } from "@hover-labs/tezos-utils"
import { generateBreakGlassStorage } from '../storage/break-glass-contract-storage'
import { generateMinterStorage } from '../storage/minter-storage'
import CACHE_KEYS from '../cache-keys'

const main = async () => {
  // Debug Info
  console.log("Migrating contracts to 1.3")
  printConfig(NETWORK_CONFIG)
  console.log('')

  // Init Deployer
  console.log("Initializing Deployer Account")
  const tezos = await getTezos(NETWORK_CONFIG)
  const deployAddress = await tezos.signer.publicKeyHash()
  console.log("Deployer initialized!")
  console.log('')

  // Load Contract Soruces
  console.log("Loading Contracts...")
  const contractSources = {
    minterSource: loadContract(`${__dirname}/../../../../smart_contracts/minter.tz`),
    breakGlassContractSource: loadContract(`${__dirname}/../../../../break-glass-contracts/smart_contracts/break-glass.tz`),
  }
  console.log("Done!")
  console.log('')


  // Deploy Pipeline

  // Step 0: Deploy a new Minter
  console.log('Deploying a new Minter')
  const minterDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.MINTER_DEPLOY, async () => {
    const minterStorage = generateMinterStorage()
    return deployContract(NETWORK_CONFIG, tezos, contractSources.minterSource, minterStorage)
  })
  console.log('')

  // Step 1: Deploy the Minter Break Glass
  console.log('Deploying a Break Glass for the new Stability Fund')
  const minterBreakGlassDeployResult: ContractOriginationResult = await fetchFromCacheOrRun(CACHE_KEYS.MINTER_BREAK_GLASS_DEPLOY, async () => {
    const breakGlassStorage = generateBreakGlassStorage(
      {
        daoAddress: KOLIBRI_CONFIG.contracts.DAO!,
        multisigAddress: KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!,
        targetAddress: minterDeployResult.contractAddress

      }
    )
    return deployContract(NETWORK_CONFIG, tezos, contractSources.breakGlassContractSource, breakGlassStorage)
  })
  console.log('')

  // Step 3: Wire the minter the break glass
  console.log('Wiring the Stability Fund to use the Break Glass as the Governor')
  const wireGovernorMinterHash: string = await fetchFromCacheOrRun(CACHE_KEYS.WIRE_STABILITY_FUND_BREAK_GLASS, async () => {
    return sendOperation(
      NETWORK_CONFIG,
      tezos,
      minterDeployResult.contractAddress,
      'setGovernorContract',
      minterBreakGlassDeployResult.contractAddress
    )
  })
  console.log('')

  // Print Results
  console.log("----------------------------------------------------------------------------")
  console.log("Operation Results")
  console.log("----------------------------------------------------------------------------")

  console.log("Contracts:")
  console.log(`New Minter Contract:              ${minterDeployResult.contractAddress} / ${minterDeployResult.operationHash}`)
  console.log(`New Minter Break Glass Contract:  ${minterBreakGlassDeployResult.contractAddress} / ${minterBreakGlassDeployResult.operationHash}`)
  console.log("")

  console.log("Operations:")
  console.log(`Wire Break Glass To Minter: ${wireGovernorMinterHash}`)

  console.log("")
}

main()