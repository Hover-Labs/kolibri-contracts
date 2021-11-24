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
  // Initial Interest Rate for Savings Pool 
  // 5% Interest
  // See https://www.wolframalpha.com/input/?i=ln%281+%2B+0.05%29+%2F+%2860+*+24+*+365%29
  initialInterestRate: new BigNumber('92827557400'),

  // Configuration for the Multisig that will become governor of the old stability fund
  stabilityFundMsig: {
    threshold: 1,
    timelockSeconds: 0,
    publicKeys: [
      "edpkvGfYw3LyB1UcCahKQk4rF2tvbMUk8GFiTuMjL75uGXrpvKXhjn", // Alice in Sandbox, tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb
    ],
  }
}