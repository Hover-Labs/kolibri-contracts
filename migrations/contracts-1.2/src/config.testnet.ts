import { KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Granada Testnet',
  tezosNodeUrl: 'https://granadanet.smartpy.io/chains/main/blocks/head/header',
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
  // Initial Interest Rate for Savings Pool 
  // 10% Interest
  // See: https://www.wolframalpha.com/input/?i=%281+%2B+0.000000181335958532%29%5E%28365+*+24+*+60%29
  initialInterestRate: new BigNumber('181335958532'),

  // Configuration for the Multisig that will become governor of the old stability fund
  stabilityFundMsig: {
    threshold: 1,
    timelockSeconds: 0,
    publicKeys: [
      'edpkuLautNoSUnM3ynaYfkPgnJD9jLKj8VvFYieipoUYx3M5kjYenx', // tz1hover5EYqdWBtwxDfNVwQ1vvZ67u3ax1N, Hover Testnet Key, held by Keefer
    ],
  }
}