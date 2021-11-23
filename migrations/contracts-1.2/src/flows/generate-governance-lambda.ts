import { fetchFromCache, compileLambda, ContractOriginationResult, getTezos, getTokenBalanceFromDefaultSmartPyContract } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, NETWORK_CONFIG } from '../config'
import CACHE_KEYS from '../cache-keys'
import BigNumber from 'bignumber.js'

const main = async () => {
    // Contracts
    const minterContract = KOLIBRI_CONFIG.contracts.MINTER!
    const oldStabilityFundContract = KOLIBRI_CONFIG.contracts.STABILITY_FUND!
    const tokenContract = KOLIBRI_CONFIG.contracts.TOKEN!

    // Break Glasses
    const minterBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.MINTER
    const stabilityFundBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.STABILITY_FUND

    // New Contracts
    const newStabilityFundContract = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress
    const stabilityFundGovernorMultisigAddress = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_MSIG) as ContractOriginationResult).contractAddress

    // Grab the current value in the stability fund.
    const tezos = await getTezos(NETWORK_CONFIG)
    const oldStabilityFundBalance: BigNumber = await getTokenBalanceFromDefaultSmartPyContract(oldStabilityFundContract, tokenContract, tezos)
    console.log(`FYI: got balance of ${JSON.stringify(oldStabilityFundBalance)}`)

    const program = `
import smartpy as sp

def setStabilityFundLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${minterContract}"),
        "setStabilityFundContract"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newStabilityFundContract}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def moveStabilityFundLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TPair(sp.TNat, sp.TAddress),
        sp.address("${oldStabilityFundContract}"),
        "sendTokens"
    ).open_some()

    param = (sp.nat(${oldStabilityFundBalance.toString()}), sp.address("${newStabilityFundContract}"))
    sp.result(
        [
            sp.transfer_operation(
                param,
                sp.mutez(0),
                contractHandle
            )
        ]
    )

def setStabilityFundGovernorLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${oldStabilityFundContract}"),
        "setGovernorContract"
    ).open_some()

    param = sp.address("${stabilityFundGovernorMultisigAddress}")
    sp.result(
        [
            sp.transfer_operation(
                param,
                sp.mutez(0),
                contractHandle
            )
        ]
    )

def governanceLambda(unit):
    sp.set_type(unit, sp.TUnit)

    minterBreakGlassHandle = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${minterBreakGlassContract}"),
        "runLambda"
    ).open_some()

    stabilityFundBreakGlassHandle = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${stabilityFundBreakGlassContract}"),
        "runLambda"
    ).open_some()

    # Note that 'moveStabilityFundLambda' needs to occur before 'setStabilityFundGovernorLambda'
    sp.result(
        [
            sp.transfer_operation(setStabilityFundLambda, sp.mutez(0), minterBreakGlassHandle),
            sp.transfer_operation(moveStabilityFundLambda, sp.mutez(0), stabilityFundBreakGlassHandle),
            sp.transfer_operation(setStabilityFundGovernorLambda, sp.mutez(0), stabilityFundBreakGlassHandle),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
