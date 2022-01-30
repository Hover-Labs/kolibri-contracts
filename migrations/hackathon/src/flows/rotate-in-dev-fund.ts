import { compileLambda, ContractOriginationResult, fetchFromCache, } from '@hover-labs/tezos-utils'
import CACHE_KEYS from '../cache-keys'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from '../config'

const main = async () => {
  // Contracts
  const minterContract = KOLIBRI_CONFIG.contracts.MINTER!
  const newDevFund = await fetchFromCache(CACHE_KEYS.DEV_FUND_DEPLOY) as ContractOriginationResult

  // Break Glasses
  const minterBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.MINTER

  const program = `
import smartpy as sp

def setDevFund(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("${minterContract}"),
        "setDeveloperFundContract"
    ).open_some()

    param = sp.address("${newDevFund.contractAddress}")

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

    minterBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("${minterBreakGlassContract}"),
        "runLambda"
    ).open_some()    

    sp.result(
        [
            sp.transfer_operation(setDevFund, sp.mutez(0), minterBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

  const compiled = compileLambda(program)

  console.log("Governance Lambda:")
  console.log(compiled)
}

main()
