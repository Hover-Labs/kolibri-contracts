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
  escrowAmount: 1000000000000000000000,
  governanceVoteLength: 10080,
  governanceTimelockLength: 4320,
}

export const MIGRATION_CONFIG = {
  // Initial Interest Rate for Savings Pool 
  // 10% Interest
  // See: https://www.wolframalpha.com/input/?i=%281+%2B+0.000000181335958532%29%5E%28365+*+24+*+60%29
  initialInterestRate: new BigNumber('181335958532'),

  // Configuration for the Multisig that will become governor of the old stability fund
  stabilityFundMsig: {
    threshold: 2,
    timelockSeconds: 0,
    publicKeys: [
      'edpkuLh768382911CBbWkCN9joZkaZinKKeqPeMnxSoUb3X4TV7GpJ', // tz1YeYpdJshsXxkPdSdKUJaF1QmH1ngCrJ7V, Keefer
      'edpktxA2V59rHy8FyHyfkiayz3y4cTYBcTWpooKJnREgBzJzLV7ZMT', // tz1Zygasw3bGh9uer7ue2KABjGFYpPsZVazZ, Luke
      'edpkuPu3FQqWPFTXRT21BBCy5pstVoM6ynwzz9SaFnr6TVrg5Z7GrK', // tz1Xh11mHYWxbYHv55AVhsPPPJeSp8PunERB, Ryan
    ],
  }
}