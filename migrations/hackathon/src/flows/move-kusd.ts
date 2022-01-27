import { compileLambda, } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
    // Contracts
    const devFundContract = KOLIBRI_CONFIG.contracts.DEVELOPER_FUND!
    const communityFundContract = KOLIBRI_CONFIG.contracts.DAO_COMMUNITY_FUND!

    // Break Glasses
    const devFundBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.DEVELOPER_FUND
    const communityFundBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.DAO_COMMUNITY_FUND

    const program = `
import smartpy as sp

def movekUSD(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TPair(sp.TNat, sp.TAddress),
        sp.address("${devFundContract}"),
        "sendTokens"
    ).open_some()

    param = (sp.nat(${MIGRATION_CONFIG.amountkUSD.toFixed()}), sp.address("${MIGRATION_CONFIG.recipient}"))

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

    devFundBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${devFundBreakGlassContract}"),
        "runLambda"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(movekUSD, sp.mutez(0), devFundBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
