import { fetchFromCache, compileLambda, ContractOriginationResult, getTezos, getTokenBalanceFromDefaultSmartPyContract } from '@hover-labs/tezos-utils'
import { KOLIBRI_CONFIG, NETWORK_CONFIG, MIGRATION_CONFIG } from '../config'
import CACHE_KEYS from '../cache-keys'
import BigNumber from 'bignumber.js'

const main = async () => {
    const farm: any = await fetchFromCache('farm')

    // Contracts
    const communityFundContract = KOLIBRI_CONFIG.contracts.DAO_COMMUNITY_FUND!

    // Break Glasses
    const communityFundBreakGlassContract = KOLIBRI_CONFIG.contracts.BREAK_GLASS_CONTRACTS.DAO_COMMUNITY_FUND!

    const program = `
import smartpy as sp

def movekDAO(unit):
    sp.set_type(unit, sp.TUnit)
    contractHandle = sp.contract(
        sp.TPair(sp.TNat, sp.TAddress),
        sp.address("${communityFundContract}"),
        "send"
    ).open_some()
    param = (sp.nat(${MIGRATION_CONFIG.farmingConfig.totalRewards.toFixed()}), sp.address("${farm.reserveDeployResult.contractAddress}"))
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

    farmHandle = sp.contract(
        sp.TNat,
        sp.address("KT1KVumbbpB58gFxDPxappP2m4QJTyZExLaE"),
        "revoke"
    ).open_some()

    sp.result(
        [
            sp.transfer_operation(sp.nat(10), sp.mutez(0), farmHandle)
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
        `

    const compiled = compileLambda(program)

    console.log("Governance Lambda:")
    console.log(compiled)
}

main()
