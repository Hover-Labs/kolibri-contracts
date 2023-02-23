import * as config from '../config'
import crosscheck from '../crosscheck'
import { generateBreakGlassStorage } from '../storage-wrappers/break-glass-contract'
import { generateMinterStorage } from '../storage-wrappers/minter-contract'
import { ContractOriginationResult, deployContract, fetchOrRun, sendOperation } from '../utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
    console.log("Migrating contracts to 1.3")

    // Step 0: Crosscheck and initialize
    const { contractSources } = await crosscheck(config)

    // Step 1: Deploy the new minter with governor set to deployer.
    console.log("Formulating Storage from Old Minter")

    const tezos = await config.getTezos()

    const minterDeployResult: ContractOriginationResult = await fetchOrRun(
        'new-minter',
        async () => {
            const minterStorage = await generateMinterStorage(
                KOLIBRI_CONFIG.contracts.MINTER!,
                KOLIBRI_CONFIG.contracts.LIQUIDITY_POOL!,
                await tezos.signer.publicKeyHash(),
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
                    daoAddress: KOLIBRI_CONFIG.contracts.DAO!,
                    multisigAddress: KOLIBRI_CONFIG.contracts.BREAK_GLASS_MULTISIG!,
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
            return sendOperation(config, minterDeployResult.contractAddress, 'setGovernorContract', breakGlassDeployResult.contractAddress)
        }
    )

    // Step 4: Output Results
    console.log("----------------------------------------------------------------------------")
    console.log("Operation Results")
    console.log("----------------------------------------------------------------------------")

    console.log("Contracts:")
    console.log(`New Minter Contract:        ${minterDeployResult.contractAddress} / ${minterDeployResult.operationHash}`)
    console.log(`New Break Glass Contract:   ${breakGlassDeployResult.contractAddress} / ${breakGlassDeployResult.operationHash}`)
    console.log("")

    console.log("Operations:")
    console.log(`Wire Minter To Break Glass: ${wireGovernorHash}`)
    console.log("")
}

main()