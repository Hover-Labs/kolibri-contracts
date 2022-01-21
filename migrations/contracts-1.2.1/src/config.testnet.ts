import { KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Granada Testnet',
  tezosNodeUrl: "https://granadanet.api.tez.ie/",
  betterCallDevUrl: 'https://api.better-call.dev/v1',
  requiredConfirmations: 2,
  maxConfirmationPollingRetries: 10,
  operationDelaySecs: 40,
}

export const KOLIBRI_CONFIG: KolibriConfig = {
  contracts: CONTRACTS.TEST,
  escrowAmount: 1,
  governanceVoteLength: 10,
  governanceTimelockLength: 6,
}

export const MIGRATION_CONFIG = {
  // Null address
  // See: https://tzkt.io/tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU/operations/
  nullAddress: "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"
}
