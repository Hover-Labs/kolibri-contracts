import { KolibriConfig, NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Mainnet',
  tezosNodeUrl: 'https://rpc.tzbeta.net/',
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
  // Initial Interest Rate for Savings Pool 
  // 0% interest - So that the DAO can set this.
  initialInterestRate: new BigNumber('0'),

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