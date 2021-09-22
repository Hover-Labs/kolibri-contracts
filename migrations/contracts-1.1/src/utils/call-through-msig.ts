import { TezosToolkit, MichelsonMap, ContractMethod } from "@taquito/taquito";
import { OpKind } from "@taquito/rpc";
import { InMemorySigner } from "@taquito/signer";
import { Parser, MichelsonType, MichelsonData } from "@taquito/michel-codec";
import BigNumber from "bignumber.js";

import { compileOperation } from '../../../../multisig-timelock/cli/src/helpers'
import { OperationData } from '../../../../multisig-timelock/cli/src/types'
import { OperationContentsTransaction } from "@taquito/rpc/dist/types/types";
import { ContractProvider } from "@taquito/taquito/dist/types/contract/interface";
import { checkConfirmed } from "../utils";

async function getNextOperationID(tezos: TezosToolkit, multiSigContractAddress: string) {
    const multiSigContract = await tezos.contract.at(multiSigContractAddress)
    const multiSigStorage: any = await multiSigContract.storage()
    const operationId: BigNumber = await multiSigStorage.operationId

    return operationId.plus(1).toNumber()
}

export async function simulateOperation(tezos: TezosToolkit, operations: ContractMethod<ContractProvider>[], sourceAddress?: string) {
    const header = await tezos.rpc.getBlockHeader();

    const signerPublicKeyHash = await tezos.signer.publicKeyHash()

    const contract = await tezos.rpc.getContract(signerPublicKeyHash);

    const formattedOperations = operations.map((op) => {
        return {
            counter: (parseInt(contract.counter || "0") + 1).toString(),
            destination: op['address'],
            kind: OpKind.TRANSACTION,
            source: sourceAddress || signerPublicKeyHash,
            fee: '0',
            gas_limit: '1040000',
            storage_limit: '60000',
            amount: '0',
            parameters: op.toTransferParams().parameter,
        } as OperationContentsTransaction
    })

    return await tezos.rpc.runOperation({
        chain_id: header.chain_id,
        operation: {
            branch: header.hash,
            signature: "sigUHx32f9wesZ1n2BWpixXz4AQaZggEtchaQNHYGRCoWNAXx45WGW2ua3apUUUAGMLPwAU41QoaFCzVSL61VaessLg4YbbP",
            contents: formattedOperations,
        },
    })
}

export async function callThroughMultisig(
    config: any,
    multiSigContractAddress: string,
    targetContract: string,
    targetEntrypoint: string,
    entrypointArgs: string
) {

    const tezos = new TezosToolkit(config.NODE_URL);
    tezos.setProvider({ signer: await InMemorySigner.fromSecretKey(config.privateKey) })

    const michelsonParser = new Parser()
    const chainID = await tezos.rpc.getChainId()
    const operationID = await getNextOperationID(tezos, multiSigContractAddress)

    const operationToSign: OperationData = {
        address: targetContract,
        argSmartPy: entrypointArgs,
        argTypeSmartPy: undefined,
        entrypoint: targetEntrypoint,
        amountMutez: 0,
    }

    const lambdaToSign = compileOperation(
        operationToSign,
        config.SMARTPY_CLI
    )

    // Pack encoded lambda
    const type = michelsonParser.parseMichelineExpression(
        '(pair chain_id (pair nat (lambda unit (list operation))))'
    ) as MichelsonType
    const encodedData = michelsonParser.parseMichelineExpression(
        `(Pair "${chainID}" (Pair ${operationID} ${lambdaToSign}))`
    ) as MichelsonData
    const packedResult = await tezos.rpc.packData({ data: encodedData, type: type })

    // Sign the operation
    const sig = await tezos.signer.sign(packedResult.packed)

    const multisigContract = await tezos.contract.at(multiSigContractAddress)

    const pkh = await tezos.signer.publicKeyHash()

    const submitCall = multisigContract.methods.submit(
        MichelsonMap.fromLiteral({
            [pkh]: sig.prefixSig
        }),
        chainID,
        operationID,
        michelsonParser.parseMichelineExpression(lambdaToSign)
    )

    const executeCall = multisigContract.methods.execute(operationID)

    console.log(`Invoking submit()...`)
    const submissionResult = await submitCall.send()
    console.log(`Injected in hash `, submissionResult.hash)

    console.log(`Awaiting confirmation...`)
    await checkConfirmed(config, submissionResult.hash)
    console.log(`Done!`)

    console.log(`Invoking execute()...`)
    const executeResult = await executeCall.send()
    console.log(`Executed in hash`, executeResult.hash)

    console.log(`Awaiting confirmation...`)
    await checkConfirmed(config, executeResult.hash)
    console.log(`Done!`)

    return { submissionResult, executeResult }
}