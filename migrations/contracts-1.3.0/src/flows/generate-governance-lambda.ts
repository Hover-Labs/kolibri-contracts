import { compileLambda, } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

import { fetchFromCache } from '../utils'

// Prior art: https://governance.kolibri.finance/proposals/4

const main = async () => {
    // Core Contracts
    const ovenProxyContract = KOLIBRI_CONFIG.contracts.OVEN_PROXY!
    const ovenFactoryContract = KOLIBRI_CONFIG.contracts.OVEN_FACTORY!
    const tokenContract = KOLIBRI_CONFIG.contracts.TOKEN!

    // Break glasses
    const ovenProxyBreakGlassContractAddress  = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.OVEN_PROXY!
    const ovenFactoryBreakGlassContractAddress = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.OVEN_FACTORY!
    const tokenBreakGlassContractAddress = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.TOKEN!

    // New artifacts
    const newMinter = (await fetchFromCache('new-minter')).contractAddress

    const program = `
import smartpy as sp

def setMinterOnOvenProxy(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${ovenProxyContract}"),
        "setMinterContract"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinter}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def setMinterOnOvenOvenFactory(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${ovenFactoryContract}"),
        "setMinterContract"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinter}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def setAdministratorOnToken(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${tokenContract}"),
        "setAdministrator"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinter}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  


def unpause(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TUnit,
        sp.address("${ovenProxyContract}"),
        "unpause"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.unit,
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def governanceLambda(unit):
    sp.set_type(unit, sp.TUnit)


    ovenProxyBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${ovenProxyBreakGlassContractAddress}"),
        "runLambda"
    ).open_some()

    ovenFactoryBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${ovenFactoryBreakGlassContractAddress}"),
        "runLambda"
    ).open_some()


    tokenBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${tokenBreakGlassContractAddress}"),
        "runLambda"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(setMinterOnOvenProxy, sp.mutez(0), ovenProxyBreakGlassLambda),
            sp.transfer_operation(setMinterOnOvenOvenFactory, sp.mutez(0), ovenFactoryBreakGlassLambda),
            sp.transfer_operation(setAdministratorOnToken, sp.mutez(0), tokenBreakGlassLambda),
            sp.transfer_operation(unpause, sp.mutez(0), ovenProxyBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
