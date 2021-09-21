"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const constants_1 = __importDefault(require("./constants"));
const conseiljs_1 = require("conseiljs");
class OperationFeeEstimator {
    constructor(tezosNodeUrl, enableZeroFees = false) {
        this.tezosNodeUrl = tezosNodeUrl;
        this.enableZeroFees = enableZeroFees;
    }
    async estimateAndApplyFees(transactions) {
        for (let i = 0; i < transactions.length; i++) {
            const transaction = transactions[i];
            transaction.fee = '0';
        }
        for (let i = 0; i < transactions.length; i++) {
            const transaction = transactions[i];
            let priorConsumedResources = {
                gas: 0,
                storageCost: 0,
            };
            if (i !== 0) {
                const priorTransactions = transactions.slice(0, i);
                priorConsumedResources = await conseiljs_1.TezosNodeWriter.estimateOperation(this.tezosNodeUrl, 'main', ...priorTransactions);
            }
            const currentTransactions = transactions.slice(0, i + 1);
            const currentConsumedResources = await conseiljs_1.TezosNodeWriter.estimateOperation(this.tezosNodeUrl, 'main', ...currentTransactions);
            const gasLimitDelta = currentConsumedResources.gas - priorConsumedResources.gas;
            const storageLimitDelta = currentConsumedResources.storageCost -
                priorConsumedResources.storageCost;
            const gasWithSafetyMargin = gasLimitDelta + constants_1.default.gasSafetyMargin;
            let storageWithSafetyMargin = storageLimitDelta + constants_1.default.storageSafetyMargin;
            if (transaction.kind === 'origination') {
                storageWithSafetyMargin += constants_1.default.originationBurnCost;
            }
            transaction.storage_limit = `${storageWithSafetyMargin}`;
            transaction.gas_limit = `${gasWithSafetyMargin}`;
        }
        const blockHead = await conseiljs_1.TezosNodeReader.getBlockAtOffset(this.tezosNodeUrl, 0);
        if (this.enableZeroFees) {
            return transactions;
        }
        let requiredFee = this.calculateRequiredFee(transactions, blockHead);
        let currentFee = this.calculateCurrentFees(transactions);
        while (currentFee < requiredFee) {
            transactions[0].fee = `${requiredFee}`;
            requiredFee = this.calculateRequiredFee(transactions, blockHead);
            currentFee = this.calculateCurrentFees(transactions);
        }
        return transactions;
    }
    calculateCurrentFees(transactions) {
        return transactions.reduce((accumulated, next) => {
            return accumulated + parseInt(next.fee);
        }, 0);
    }
    calculateRequiredFee(transactions, block) {
        const requiredGasFeeNanotez = this.calculateGasFees(transactions);
        const operationSize = this.calculateSerializedByteLength(transactions, block);
        const storageFeeNanotez = constants_1.default.feePerByteNanotez * operationSize;
        const requiredFeeNanotez = constants_1.default.minimumFeeNanotez + requiredGasFeeNanotez + storageFeeNanotez;
        const requiredFeeMutez = Math.ceil(requiredFeeNanotez / constants_1.default.nanotezPerMutez);
        return requiredFeeMutez;
    }
    calculateGasFees(transactions) {
        return transactions.reduce((accumulated, next) => {
            return (accumulated + parseInt(next.gas_limit) * constants_1.default.feePerGasUnitNanotez);
        }, 0);
    }
    calculateSerializedByteLength(transactions, block) {
        const forgedOperationGroup = conseiljs_1.TezosNodeWriter.forgeOperations(block.hash, transactions);
        const size = forgedOperationGroup.length / 2 + constants_1.default.signatureSizeBytes;
        return size;
    }
}
exports.default = OperationFeeEstimator;
//# sourceMappingURL=operation-fee-estimator.js.map