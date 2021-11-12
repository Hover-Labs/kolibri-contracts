/** TODO(keefertaylor): Push into tezos-utils */

import { NetworkConfig, checkConfirmed, } from "@hover-labs/tezos-utils";
import { TezosToolkit } from "@taquito/taquito";
import BigNumber from 'bignumber.js'

/**
 * Approve an allowance for an FA1.2 token
 * 
 * @param spender The account who can spend
 * @param amount TThe amount to spend
 * @param tokenContractAddress The address of the token that will be spent.
 * @param tezos A toolkit. The signer of this toolkit will be the one issuing the approval
 * @param config The network config.
 * @returns 
 */
export const approveToken = async (spender: string, amount: BigNumber, tokenContractAddress: string, tezos: TezosToolkit, config: NetworkConfig): Promise<string> => {
  const tokenContract = await tezos.contract.at(tokenContractAddress)
  const result = await tokenContract.methods.approve(spender, amount).send()
  await checkConfirmed(config, result.hash)
  return result.hash
}