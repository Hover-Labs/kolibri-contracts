// General config for a sandbox.
import { TezosToolkit } from "@taquito/taquito";
import { InMemorySigner } from "@taquito/signer";
import { KolibriCoreContracts } from "./kolibri-core-contracts";
import { CONTRACTS } from "@hover-labs/kolibri-js";

export const MANTISSA = Math.pow(10, 18)
export const XTZ_MANTISSA = Math.pow(10, 6)

export const LOG_LEVEL = 'info'

// Network configuration
export let NODE_URL = "https://sandbox.hover.engineering/"
export let BETTER_CALL_DEV_BASE_URL = "https://bcd.hover.engineering/"
export let OPERATION_DELAY_SECS = 10

// Max retries for confirming transactions
export const MAX_RETRIES_FOR_CONFIRMATION_POLLING = 10

// Number of confirmations required
export const NUMBER_OF_CONFIRMATIONS = 2

// Contracts to use for Core.
export const coreContracts: KolibriCoreContracts = CONTRACTS.TEST
// Break glass contracts
// TODO(keefertaylor): Should these be a list somewhere?
export const breakGlassContracts = {
    OVEN_FACTORY: "",
    OVEN_PROXY: "",
    TOKEN: "",
}

// Deployer configuration
export const privateKeyName = 'DEPLOY_SK'
export const privateKey = process.env[privateKeyName] || ''
if (privateKey === '') {
    throw new Error(`Private key envar ${privateKeyName} must be set for operation!`)
}

// The location of the SmartPy CLI
export const SMARTPY_CLI = '~/smartpy-cli/SmartPy.sh'

// The address of a vesting vault that can pass governance proposals
export const VESTING_VAULT_ADDRESS = ''

// New Configuration
export const PRIVATE_OWNER_LIQUIDATION_THRESHOLD = 180 * MANTISSA // 180%

const Tezos = new TezosToolkit(NODE_URL);
let initialized = false;
export async function getTezos() {
    if (!initialized) {
        Tezos.setProvider({ signer: await InMemorySigner.fromSecretKey(privateKey) })
    }
    return Tezos
}