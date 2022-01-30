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
  const kUSDContract = KOLIBRI_CONFIG.contracts.TOKEN

  // Load recipient
  const recipient = MIGRATION_CONFIG.recipient

  // Check that they own the correct amount of tokens
  if ((await getTokenBalanceFromDefaultSmartPyContract(recipient, kUSDContract, tezos)).isEqualTo(MIGRATION_CONFIG.amountkUSD)) {
    throw new Error("Recipient doesn't have the right amount of kUSD")
  }
}
main()