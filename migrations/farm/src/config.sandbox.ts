import { CONSTANTS, KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
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
  farmingConfig: {
    inputTokenAddress: 'KT1PRFhWsUTpZPdFfBgLVwVEtUYrv33VDTRw',
    totalRewards: new BigNumber(1000 * CONSTANTS.MANTISSA),
    rewardPerBlock: new BigNumber(1 * CONSTANTS.MANTISSA),
    totalBlocks: new BigNumber(3000),
  }
}