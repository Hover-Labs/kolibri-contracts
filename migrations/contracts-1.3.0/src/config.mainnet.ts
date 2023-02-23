import { KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Mainnet',
  tezosNodeUrl: 'https://mainnet.smartpy.io',
  betterCallDevUrl: 'https://api.better-call.dev/v1',
  requiredConfirmations: 2,
  maxConfirmationPollingRetries: 10,
  operationDelaySecs: 40,
}

export const KOLIBRI_CONFIG: KolibriConfig = {
  contracts: CONTRACTS.MAIN,
  escrowAmount: 1000000000000000000000,
  governanceVoteLength: 10080,
  governanceTimelockLength: 4320,
}

export const MIGRATION_CONFIG = {
  // Null address
  // See: https://tzkt.io/tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU/operations/
  nullAddress: "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"
}
