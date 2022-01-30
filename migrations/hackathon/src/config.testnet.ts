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
  recipient: "KT1ABbTyFcAUsqo5d59ppUswQG8WxucrDGBd",
  amountkUSD: new BigNumber(9001000000000000000000),
  amountkDAO: new BigNumber(741000000000000000000),

  newSavingsRate: new BigNumber(2468),
  newStabilityFee: new BigNumber(13579)
}

