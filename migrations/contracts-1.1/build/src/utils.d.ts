import { BigNumber } from 'bignumber.js';
import { LogLevelDesc } from 'loglevel';
import { TezosToolkit, TransactionWalletOperation } from "@taquito/taquito";
import { TransactionOperation } from "@taquito/taquito/dist/types/operations/transaction-operation";
import { OperationBatch } from "@taquito/taquito/dist/types/batch/rpc-batch-provider";
export interface ContractOriginationResult {
    operationHash: string;
    contractAddress: string;
}
export declare function loadContract(filename: string): string;
export declare function initConseil(conseilLogLevel: LogLevelDesc): void;
export declare function sendOperation(config: any, contractAddress: string, entrypoint: string, parameter: string | BigNumber | null | any[], amount?: number, batch?: OperationBatch): Promise<string | undefined>;
export declare function deployContract(config: any, contractSource: string, storage: string): Promise<ContractOriginationResult>;
export declare const checkConfirmed: (config: any, operationHash: string) => Promise<void>;
export declare function objectToMichelson(obj: any): string;
export declare function transactionIsTransactionResult(tx: TransactionOperation | TransactionWalletOperation): tx is TransactionOperation;
export declare function opHashFromTaquito(input: TransactionOperation | TransactionWalletOperation): string;
export declare function fetchOrRun(key: string, runFunction: () => any): Promise<any>;
export declare function fetchFromCache(key: string): Promise<any>;
export declare function getCache(): Promise<any>;
export declare function getTokenBalance(address: string, kDAOAddress: string, config: any): Promise<BigNumber>;
export declare const executeGovProposal: (vestingVaultContractAddress: string, breakGlassContract: string | null, targetAddress: string, entryPoint: string, entryArguments: string, entryArgumentType: string, daoAddress: string, tezos: TezosToolkit, config: any) => Promise<void>;
