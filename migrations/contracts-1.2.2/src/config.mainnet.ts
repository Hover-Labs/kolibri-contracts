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
  // Initial Interest Rate for Savings Pool 
  // 0% interest - So that the DAO can set this.
  initialInterestRate: new BigNumber('0'),

  // Configuration for the Multisig that will become governor of the old stability fund
  stabilityFundMsig: {
    threshold: 2,
    timelockSeconds: 0,
    publicKeys: [
      'edpkvVfi9djFLdHaHwAJLygUDYYPsv3M7JhJxYZEGrWCi6y1Q8rEDG', // Discord:yoursoulismine, Community Member
      'edpktrq8HSok3LaMHuK17kn8yShsC5AQnpb4WKkYApQcHZNAsewt5B', // Gabe Cohen, Community Member & Founder at EcoMint
      'edpkuLh768382911CBbWkCN9joZkaZinKKeqPeMnxSoUb3X4TV7GpJ', // Keefer Taylor, Hover Labs
    ],
  }
}