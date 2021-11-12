import { fetchFromCache, compileLambda, ContractOriginationResult, getTezos, getTokenBalanceFromDefaultSmartPyContract } from '@hover-labs/tezos-utils'
import { NETWORK_CONFIG } from '../config'
import CACHE_KEYS from '../cache-keys'
import BigNumber from 'bignumber.js'

const main = async () => {
    // Contracts
    const minterContract = NETWORK_CONFIG.contracts.MINTER!
    const stabilityFundContract = NETWORK_CONFIG.contracts.STABILITY_FUND!
    const tokenContract = NETWORK_CONFIG.contracts.TOKEN!

    // Break Glasses
    const minterBreakGlassContract = NETWORK_CONFIG.contracts.BREAK_GLASS_CONTRACTS.MINTER
    const stabilityFundBreakGlassContract = NETWORK_CONFIG.contracts.BREAK_GLASS_CONTRACTS.STABILITY_FUND

    // New Stability fund contract
    const newStabilityFundContract = (await fetchFromCache(CACHE_KEYS.STABILITY_FUND_DEPLOY) as ContractOriginationResult).contractAddress

    // Grab the current value in the stability fund.
    const tezos = await getTezos(NETWORK_CONFIG)
    const stabilityFundBalance: BigNumber = await getTokenBalanceFromDefaultSmartPyContract(stabilityFundContract, tokenContract, tezos)
    console.log(`FYI: got balance of ${JSON.stringify(stabilityFundBalance)}`)

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
        sp.address("${stabilityFundContract}"),
        "sendTokens"
    ).open_some()

    param = (sp.nat(${stabilityFundBalance.toString()}), sp.address("${newStabilityFundContract}"))
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

    sp.result(
        [
            sp.transfer_operation(setStabilityFundLambda, sp.mutez(0), minterBreakGlassHandle),
            sp.transfer_operation(moveStabilityFundLambda, sp.mutez(0), stabilityFundBreakGlassHandle),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
