// General config for mainnet.
import { TezosToolkit } from "@taquito/taquito";
import { InMemorySigner } from "@taquito/signer";
import { CONTRACTS, ContractGroup } from "@hover-labs/kolibri-js";
import BigNumber from "bignumber.js";

export const MANTISSA = Math.pow(10, 18)
export const XTZ_MANTISSA = Math.pow(10, 6)

export const LOG_LEVEL = 'info'

// Network configuration
export let NODE_URL = "https://rpctest.tzbeta.net"
export let BETTER_CALL_DEV_BASE_URL = "https://api.better-call.dev/v1"
export let OPERATION_DELAY_SECS = 20

// Max retries for confirming transactions
export const MAX_RETRIES_FOR_CONFIRMATION_POLLING = 10

// Number of confirmations required
export const NUMBER_OF_CONFIRMATIONS = 1

// Contracts to use for Core.
export const coreContracts: ContractGroup = CONTRACTS.TEST

// Governance parameters
export const GOV_PARAMS = {
  quorum: new BigNumber(1).times(MANTISSA), // 1 kDAO
  voteLengthBlocks: new BigNumber('10'),
  blocksInTimelockForExecution: new BigNumber('6')
}

// Deployer configuration
export const privateKeyName = 'DEPLOY_SK'
export const privateKey = process.env[privateKeyName] || ''
if (privateKey === '') {
  throw new Error(`Private key envar ${privateKeyName} must be set for operation!`)
}

// The location of the SmartPy CLI
export const SMARTPY_CLI = '~/smartpy-cli/SmartPy.sh'

// New Configuration
export const PRIVATE_OWNER_LIQUIDATION_THRESHOLD = 20 * MANTISSA // 20%

const Tezos = new TezosToolkit(NODE_URL);
let initialized = false;
export async function getTezos() {
  if (!initialized) {
    Tezos.setProvider({ signer: await InMemorySigner.fromSecretKey(privateKey) })
  }
  return Tezos
}