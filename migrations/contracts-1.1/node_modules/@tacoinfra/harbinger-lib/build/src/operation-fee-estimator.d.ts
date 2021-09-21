import { StackableOperation } from 'conseiljs';
export default class OperationFeeEstimator {
    private readonly tezosNodeUrl;
    private readonly enableZeroFees;
    constructor(tezosNodeUrl: string, enableZeroFees?: boolean);
    estimateAndApplyFees(transactions: Array<StackableOperation>): Promise<Array<StackableOperation>>;
    private calculateCurrentFees;
    private calculateRequiredFee;
    private calculateGasFees;
    private calculateSerializedByteLength;
}
