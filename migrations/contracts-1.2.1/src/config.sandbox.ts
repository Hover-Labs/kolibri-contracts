import { KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Sandboxnet',
  tezosNodeUrl: 'https://sandbox.hover.engineering/',
  betterCallDevUrl: 'https://bcd.hover.engineering/v1',
  requiredConfirmations: 2,
  maxConfirmationPollingRetries: 10,
  operationDelaySecs: 10,
}

export const KOLIBRI_CONFIG: KolibriConfig = {
  contracts: CONTRACTS.SANDBOX,
  escrowAmount: 3000000000000000000000,
  governanceVoteLength: 15,
  governanceTimelockLength: 11,
}

export const MIGRATION_CONFIG = {
  // Null address
  // See: https://tzkt.io/tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU/operations/
  nullAddress: "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"
}
