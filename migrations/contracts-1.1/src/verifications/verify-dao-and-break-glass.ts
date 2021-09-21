import BigNumber from 'bignumber.js'
import * as config from '../config'
import { executeGovProposal, fetchFromCache } from '../utils'
import { callThroughMultisig } from "../utils/call-through-msig"
import crosscheck from '../crosscheck'

const main = async () => {
    console.log("Initializing...")
    const { keystore } = await crosscheck(config)
    const tezos = await config.getTezos()

    console.log("Loading results of deploy from cache")
    const newMinterContractAddress = (await fetchFromCache('new-minter')).contractAddress
    const breakGlassContractAddress = (await fetchFromCache('new-minter-break-glass')).contractAddress

    console.log("Passing a DAO proposal to set stability fee to zero...")
    await executeGovProposal(
        config.coreContracts.VESTING_CONTRACTS[keystore.publicKeyHash]!,
        breakGlassContractAddress,
        newMinterContractAddress,
        'setStabilityFee',
        `sp.nat(0)`,
        'sp.TNat',
        config.coreContracts.DAO_TOKEN,
        config.coreContracts.DAO,
        tezos,
        config
    )
    console.log("   > Executed proposal")
    console.log("")

    console.log("Validating Governance Result Applied")
    const newMinterContract = await tezos.contract.at(newMinterContractAddress)
    let newMinterStorage: any = await newMinterContract.storage()
    const stabilityFee: BigNumber = newMinterStorage.stabilityFee
    if (!stabilityFee.isEqualTo(0)) {
        throw new Error("Governance proposal did not apply correctly!")
    }
    console.log("   > Validated")
    console.log("")

    console.log("Breaking Glass")
    await breakGlass(breakGlassContractAddress, config.coreContracts.BREAK_GLASS_MULTISIG!, keystore.publicKeyHash)
    console.log("   > Done")

    console.log("Validating Break Glass Applied")
    // Refetch minter storage to pick up updates.
    newMinterStorage = await newMinterContract.storage()
    if (newMinterStorage.governorContractAddress !== keystore.publicKeyHash) {
        throw new Error("Breaking glass was not successful!")
    }
    console.log("   > Validated")
    console.log("")

    console.log("All tests pass!")
}

const breakGlass = async (
    breakGlassAddress: string,
    multisigAddress: string,
    newGovernor: string,
) => {
    return await callThroughMultisig(
        config,
        multisigAddress,
        breakGlassAddress,
        'breakGlass',
        `sp.address("${newGovernor}")`
    )
}

main()