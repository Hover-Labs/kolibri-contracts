import { compileLambda, } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
  // Contracts
  const savingsContract = KOLIBRI_CONFIG.contracts.SAVINGS_POOL!

  // Break Glasses
  const savingsPoolBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.SAVINGS_POOL

  const program = `
import smartpy as sp

def setSavingsRate(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TNat,
        sp.address("${savingsContract}"),
        "setInterestRate"
    ).open_some()

    param = sp.nat(${MIGRATION_CONFIG.newSavingsRate})

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

    savingsRateBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${savingsPoolBreakGlassContract}"),
        "runLambda"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(setSavingsRate, sp.mutez(0), savingsRateBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

  const compiled = compileLambda(program)

  console.log("Governance Lambda:")
  console.log(compiled)
}

main()
