"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getTezos = exports.PRIVATE_OWNER_LIQUIDATION_THRESHOLD = exports.SMARTPY_CLI = exports.privateKey = exports.privateKeyName = exports.GOV_PARAMS = exports.coreContracts = exports.NUMBER_OF_CONFIRMATIONS = exports.MAX_RETRIES_FOR_CONFIRMATION_POLLING = exports.OPERATION_DELAY_SECS = exports.BETTER_CALL_DEV_BASE_URL = exports.NODE_URL = exports.LOG_LEVEL = exports.XTZ_MANTISSA = exports.MANTISSA = void 0;
const taquito_1 = require("@taquito/taquito");
const signer_1 = require("@taquito/signer");
const kolibri_js_1 = require("@hover-labs/kolibri-js");
const bignumber_js_1 = __importDefault(require("bignumber.js"));
exports.MANTISSA = Math.pow(10, 18);
exports.XTZ_MANTISSA = Math.pow(10, 6);
exports.LOG_LEVEL = 'info';
exports.NODE_URL = "https://sandbox.hover.engineering/";
exports.BETTER_CALL_DEV_BASE_URL = "https://bcd.hover.engineering/v1";
exports.OPERATION_DELAY_SECS = 10;
exports.MAX_RETRIES_FOR_CONFIRMATION_POLLING = 10;
exports.NUMBER_OF_CONFIRMATIONS = 2;
exports.coreContracts = kolibri_js_1.CONTRACTS.SANDBOX;
exports.GOV_PARAMS = {
    escrowAmount: new bignumber_js_1.default('3000000000000000000000'),
    voteLengthBlocks: new bignumber_js_1.default('15'),
    blocksInTimelockForExecution: new bignumber_js_1.default('11')
};
exports.privateKeyName = 'DEPLOY_SK';
exports.privateKey = process.env[exports.privateKeyName] || '';
if (exports.privateKey === '') {
    throw new Error(`Private key envar ${exports.privateKeyName} must be set for operation!`);
}
exports.SMARTPY_CLI = '~/smartpy-cli/SmartPy.sh';
exports.PRIVATE_OWNER_LIQUIDATION_THRESHOLD = 20 * exports.MANTISSA;
const Tezos = new taquito_1.TezosToolkit(exports.NODE_URL);
let initialized = false;
async function getTezos() {
    if (!initialized) {
        Tezos.setProvider({ signer: await signer_1.InMemorySigner.fromSecretKey(exports.privateKey) });
    }
    return Tezos;
}
exports.getTezos = getTezos;
//# sourceMappingURL=config.sandbox.js.map