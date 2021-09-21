import * as config from '../config'
import crosscheck from '../crosscheck'
import { generateBreakGlassStorage } from '../storage-wrappers/break-glass-contract'
import { generateMinterStorage } from '../storage-wrappers/minter-contract'
import { ContractOriginationResult, deployContract, fetchOrRun, sendOperation } from '../utils'

const main = async () => {
    console.log("Migrating contracts to 1.1")

    // Step 0: Crosscheck and initialize
    const { keystore, contractSources } = await crosscheck(config)

    // Step 1: Deploy the new minter with governor set to deployer.
    console.log("Formulating Storage from Old Minter")
    console.log(`(Old Minter Contract: ${config.coreContracts.MINTER})`)
    const minterDeployResult: ContractOriginationResult = await fetchOrRun(
        'new-minter',
        async () => {
            const minterStorage = await generateMinterStorage(
                config.coreContracts.MINTER!,
                config.coreContracts.LIQUIDITY_POOL!,
                keystore.publicKeyHash,
                config.PRIVATE_OWNER_LIQUIDATION_THRESHOLD,
                config
            )
            return deployContract(config, contractSources.newMinterContractSource, minterStorage)
        }
    )

    // Step 2
    console.log("Deploying a new Break Glass")
    const breakGlassDeployResult: ContractOriginationResult = await fetchOrRun(
        'new-minter-break-glass',
        async () => {
            const breakGlassStorage = generateBreakGlassStorage(
                {
                    daoAddress: config.coreContracts.DAO!,
                    multisigAddress: config.coreContracts.BREAK_GLASS_MULTISIG!,
                    targetAddress: minterDeployResult.contractAddress

                }
            )
            return deployContract(config, contractSources.breakGlassContractSource, breakGlassStorage)
        }
    )

    // Step 3: Wire the minter to accept commands from the break glass
    console.log("Setting Minter to be governed by break glass")
    const wireGovernorHash: string = await fetchOrRun(
        'wire-governor',
        async () => {
            return sendOperation(config, minterDeployResult.contractAddress, 'setGovernorContractAddress', breakGlassDeployResult.contractAddress)
        }
    )

    // Step 4: Output Results
    console.log("----------------------------------------------------------------------------")
    console.log("Operation Results")
    console.log("----------------------------------------------------------------------------")

    console.log("Contracts:")
    console.log(`New Minter Contract:        ${minterDeployResult.contractAddress} / ${minterDeployResult.operationHash}`)
    console.log(`New Break Glass Contract:   ${breakGlassDeployResult.contractAddress} / ${breakGlassDeployResult.operationHash}`)

    console.log("Operations:")
    console.log(`Wire Minter To Break Glass: ${wireGovernorHash}`)
    console.log("")
}

main()