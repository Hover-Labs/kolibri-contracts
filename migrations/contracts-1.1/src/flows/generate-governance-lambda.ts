import * as config from '../config'
import { fetchFromCache } from '../utils'
import { compileLambda } from '../utils/compile-break-glass-lambda'

const main = async () => {
    // Contracts
    const ovenFactoryContract = config.coreContracts.OVEN_FACTORY
    const ovenProxyContract = config.coreContracts.OVEN_PROXY
    const tokenContract = config.coreContracts.TOKEN

    // Break Glasses
    const ovenFactoryBreakGlassContract = config.breakGlassContracts.OVEN_FACTORY
    const ovenProxyBreakGlassContract = config.breakGlassContracts.OVEN_PROXY
    const tokenBreakGlassContract = config.breakGlassContracts.TOKEN

    // New minter contract
    const newMinterContract = (await fetchFromCache('new-minter')).contractAddress

    const program = `
import smartpy as sp

def ovenFactoryLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${ovenFactoryContract}"),
        "setMinterContract"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinterContract}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def ovenProxyLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${ovenProxyContract}"),
        "setMinterContract"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinterContract}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )

def tokenLambda(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${tokenContract}"),
        "setAdministrator"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(
                sp.address("${newMinterContract}"),
                sp.mutez(0),
                contractHandle
            )
        ]
    )        

def governanceLambda(unit): 
    sp.set_type(unit, sp.TUnit)

    ovenFactoryBreakGlassHandle = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${ovenFactoryBreakGlassContract}"),
        "runLambda"
    ).open_some()

    ovenProxyBreakGlassHandle = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${ovenProxyBreakGlassContract}"),
        "runLambda"
    ).open_some()

    tokenBreakGlassHandle = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${tokenBreakGlassContract}"),
        "runLambda"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(ovenFactoryLambda, sp.mutez(0), ovenFactoryBreakGlassHandle),
            sp.transfer_operation(ovenProxyLambda, sp.mutez(0), ovenProxyBreakGlassHandle),
            sp.transfer_operation(tokenLambda, sp.mutez(0), tokenBreakGlassHandle)
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
`

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
