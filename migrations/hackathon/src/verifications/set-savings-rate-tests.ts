import { approveToken, checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS, sendOperation } from "@hover-labs/tezos-utils"
import { NETWORK_CONFIG } from "../config"
import _ from "lodash";
import { TransactionWalletOperation } from '@taquito/taquito'
import { KOLIBRI_CONFIG, MIGRATION_CONFIG } from "../config"

const main = async () => {
  console.log("Validating end state is correct")
  console.log("")

  // Load contracts
  const tezos = await getTezos(NETWORK_CONFIG)
  const savingsContract = KOLIBRI_CONFIG.contracts.SAVINGS_POOL

  // Check the savings rate matches the new rate.
  await validateStorageValue(savingsContract, 'interestRate', MIGRATION_CONFIG.newSavingsRate, tezos)
}
main()