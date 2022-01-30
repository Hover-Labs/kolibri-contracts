import { compileLambda, } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
    // Contracts
    const communityFundContract = KOLIBRI_CONFIG.contracts.DAO_COMMUNITY_FUND!

    // Break Glasses
    const communityFundBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.DAO_COMMUNITY_FUND

    const program = `
import smartpy as sp

def movekDAO(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TPair(sp.TNat, sp.TAddress),
        sp.address("${communityFundContract}"),
        "send"
    ).open_some()

    param = (sp.nat(${MIGRATION_CONFIG.amountkDAO.toFixed()}), sp.address("${MIGRATION_CONFIG.recipient}"))

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

    communityFundBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${communityFundBreakGlassContract}"),
        "runLambda"
    ).open_some()    

    sp.result(
        [
            sp.transfer_operation(movekDAO, sp.mutez(0), communityFundBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
