import { compileLambda, } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
    // Contracts
    const liquidityPoolContract = KOLIBRI_CONFIG.contracts.LIQUIDITY_POOL!

    // Break Glasses
    const liquidityPoolBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.LIQUIDITY_POOL

    // Null address
    const nullAdddress = MIGRATION_CONFIG.nullAddress

    const program = `
import smartpy as sp

def setQuipuswapPoolLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${liquidityPoolContract}"),
        "updateQuipuswapAddress"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${nullAdddress}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def governanceLambda(unit):
    sp.set_type(unit, sp.TUnit)

    liquidityPoolBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${liquidityPoolBreakGlassContract}"),
        "runLambda"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(setQuipuswapPoolLambda, sp.mutez(0), liquidityPoolBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
