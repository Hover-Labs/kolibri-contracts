import fetch from 'node-fetch'
import path from 'path'
import fs from 'fs'
import { BigNumber } from 'bignumber.js'
import { getLogger, LogLevelDesc } from 'loglevel'
import { registerFetch, registerLogger, TezosMessageUtils } from 'conseiljs'

import { TezosToolkit, TransactionWalletOperation } from "@taquito/taquito"
import { TransactionOperation } from "@taquito/taquito/dist/types/operations/transaction-operation"
import { OperationBatch } from "@taquito/taquito/dist/types/batch/rpc-batch-provider"

import { Utils } from '@tacoinfra/harbinger-lib'
import { compileBreakGlassOperation } from "./utils/compile-break-glass-lambda";
import { Parser } from "@taquito/michel-codec";

const axios = require('axios').default;

const CACHE_FILE = path.join(__dirname, '../deploy-data.json')

export interface ContractOriginationResult {
    operationHash: string
    contractAddress: string
}

export function loadContract(filename: string): string {
    return fs.readFileSync(filename).toString()
}

export function initConseil(conseilLogLevel: LogLevelDesc): void {
    const logger = getLogger('conseiljs')
    logger.setLevel(conseilLogLevel, false)

    registerLogger(logger)
    registerFetch(fetch)
}

export async function sendOperation(
    config: any,
    contractAddress: string,
    entrypoint: string,
    parameter: string | BigNumber | null | any[],
    amount: number = 0,
    batch?: OperationBatch
): Promise<string | undefined> {
    try {
        console.log(`Using amount: ${amount}`)
        console.log(`Using param: ${parameter}`)

        const Tezos = await config.getTezos()

        console.log("Using address: " + contractAddress)
        const contract = await Tezos.contract.at(contractAddress)


        console.log("DEBUG: " + JSON.stringify(contract.methods))
        console.log("Entrypoint..." + entrypoint)

        let invocation
        if (Array.isArray(parameter)) {

            invocation = contract.methods[entrypoint].apply(null, parameter)
        } else if (parameter === null) {
            invocation = contract.methods[entrypoint]()
        } else {
            invocation = contract.methods[entrypoint](parameter)
        }

        if (batch !== undefined) {
            batch.withContractCall(invocation)
        } else {
            let result
            if (amount !== 0) {
                result = await invocation.send({ amount, mutez: true })
            } else {
                result = await invocation.send()
            }
            console.log(`Deployed in hash: ${result.hash}`)
            console.log('')

            console.log("Awaiting confirmation...")
            await checkConfirmed(config, result.hash)
            console.log("Confirmed!")

            return result.hash
        }

    } catch (e) {
        console.log('Caught exception, retrying...')
        console.log(e.message)
        console.error(e)
        await Utils.sleep(config.OPERATION_DELAY_SECS)

        return sendOperation(
            config,
            contractAddress,
            entrypoint,
            parameter,
            amount
        )
    }
}

export async function deployContract(
    config: any, contractSource: string,
    storage: string,
): Promise<ContractOriginationResult> {
    try {
        console.log(`Using storage: ${storage}`)

        const Tezos = await config.getTezos()

        const result = await Tezos.contract.originate({
            code: contractSource,
            init: storage,
        })

        console.log(`Deployed in hash: ${result.hash}`)
        console.log(`Deployed contract: ${result.contractAddress}`)
        console.log('')

        console.log("Awaiting confirmation...")
        await checkConfirmed(config, result.hash)
        console.log("Confirmed!")

        return {
            operationHash: result.hash,
            contractAddress: result.contractAddress || "ERR",
        }
    } catch (e) {
        console.log('Caught exception, retrying...')
        console.error(e)
        debugger;
        console.log(e.message)
        await Utils.sleep(config.OPERATION_DELAY_SECS)

        return deployContract(
            config, contractSource,
            storage,
        )
    }
}

export const checkConfirmed = async (config: any, operationHash: string): Promise<void> => {
    // Sleep for the number of blocks to try to get a confirmation without error-ing.
    await Utils.sleep((config.NUMBER_OF_CONFIRMATIONS) * config.OPERATION_DELAY_SECS)

    const operationStatusUrl = `${config.BETTER_CALL_DEV_BASE_URL}/opg/${operationHash}`
    const headUrl = `${config.NODE_URL}/chains/main/blocks/head/header`

    for (let currentTry = 0; currentTry < config.MAX_RETRIES_FOR_CONFIRMATION_POLLING; currentTry++) {
        try {
            // Get operation data
            const operationDataResult = await axios.get(operationStatusUrl)
            if (operationDataResult.status != 200) {
                throw new Error(`Got status code ${operationDataResult.status} when querying operation status`)
            }
            // Note: This API returns an array of operations which might have differing data (ex. gas, storage consumption).
            // Since operation groups are applied atomically and all data we care about (level, status) are the same on an
            // atomic operation, we simply look at the first element.
            const operationData = operationDataResult.data[0]

            // Get explorer head
            const headResult = await axios.get(headUrl)
            if (headResult.status != 200) {
                throw new Error(`Got status code ${headResult.status} when querying operation status.`)
            }
            const headData = headResult.data

            // Operation must be applied.
            if (operationData.status !== 'applied') {
                throw new Error(`Operation is not applied! Current status: ${operationData.status}`)
            }

            // Require the right number of confirmations.
            const headLevel = new BigNumber(headData.level)
            const operationLevel = new BigNumber(operationData.level)
            const delta = headLevel.minus(operationLevel)
            if (delta.isLessThan(config.NUMBER_OF_CONFIRMATIONS)) {
                throw new Error(`Did not have required number of confirmations. Head: ${headLevel.toFixed()}, Operation: ${operationLevel.toFixed()}`)
            }

            // If we've made it here without an error, then all tests have passed and the operation has confirmed.
            return
        } catch (e) {
            // Something above didn't track - that's probably okay since the network sometimes runs slow.
            // Print the error and sleep for another block before trying again.
            console.log(`Caught exception while polling ${e}`)
            console.log(`(Try ${currentTry + 1} of ${config.MAX_RETRIES_FOR_CONFIRMATION_POLLING})`)
            await Utils.sleep(config.OPERATION_DELAY_SECS)
        }
    }

    // All retries have been exhausted and at this point something is probably borked and we want to crash the program.
    throw new Error(`Could not confirm operation ${operationHash}`)
}


const char2Bytes = (str: string) => "0x" + Buffer.from(str, "utf8").toString("hex");

export function objectToMichelson(obj: any) {
    const data = []
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            if (typeof obj[key] !== 'string') {
                throw new Error("Can not serialize anything but string values!")
            }
            if (isNaN(parseInt(key))) {
                data.push(`Elt "${key}" ${char2Bytes(obj[key])}`)
            } else {
                data.push(`Elt ${key} ${char2Bytes(obj[key])}`)
            }
        }
    }
    return `{ ${data.join("; ")} }`
}

export function transactionIsTransactionResult(tx: TransactionOperation | TransactionWalletOperation): tx is TransactionOperation {
    return (tx as TransactionOperation).hash !== undefined;
}

export function opHashFromTaquito(input: TransactionOperation | TransactionWalletOperation): string {
    if (transactionIsTransactionResult(input)) {
        return input.hash
    } else {
        return input.opHash
    }
}

export async function fetchOrRun(key: string, runFunction: () => any) {
    const deployCache = await getCache()

    if (deployCache.hasOwnProperty(key)) {
        console.log(`Loaded '${key}' from the cache!`)
        return deployCache[key]
    } else {
        let result = await runFunction()

        // If we have a void function, just set *something* json serializable (undefined is not)
        if (result === undefined) {
            result = true
        }

        deployCache[key] = result

        fs.writeFileSync(CACHE_FILE, JSON.stringify(deployCache, null, 2))
        return result
    }
}

export async function fetchFromCache(key: string) {
    const deployCache = await getCache()
    if (deployCache.hasOwnProperty(key)) {
        return deployCache[key]
    } else {
        throw new Error(`key '${key}' not found in cache`)
    }
}

export async function getCache() {
    if (!fs.existsSync(CACHE_FILE)) {
        console.log("Creating a new deploy cache")
        fs.writeFileSync(CACHE_FILE, JSON.stringify({
            created: new Date()
        }))
    }

    return JSON.parse(fs.readFileSync(CACHE_FILE).toString())
}

// Get a token balance.
export async function getTokenBalance(address: string, kDAOAddress: string, config: any): Promise<BigNumber> {
    const tezos = await config.getTezos()
    const tokenContract = await tezos.contract.at(kDAOAddress)
    const tokenStorage: any = await tokenContract.storage()
    const balance = await tokenStorage.balances.get(address)

    return balance === undefined ? new BigNumber(0) : balance
}

export const executeGovProposal = async (
    vestingVaultContractAddress: string,
    breakGlassContract: string | null,
    targetAddress: string,
    entryPoint: string,
    entryArguments: string,
    entryArgumentType: string,
    kDAOToken: any,
    dao: any,
    tezos: TezosToolkit,
    config: any
) => {
    const vestingVaultContract = await tezos.contract.at(vestingVaultContractAddress)

    let compiledLambda: string
    if (breakGlassContract !== null) {
        console.log(`  - Compiling break glass operation...`)
        compiledLambda = compileBreakGlassOperation(
            targetAddress, entryPoint, entryArguments,
            entryArgumentType, breakGlassContract as string
        )
    } else {
        throw new Error("Tried to compile a non-break glass lambda!")
    }

    const michelsonParser = new Parser()
    const lambdaObject = michelsonParser.parseMichelineExpression(compiledLambda)

    console.log("  - Submitting proposal...")
    const proposalSubmission = tezos.contract.batch([])
        .withContractCall(
            vestingVaultContract.methods.propose(
                config.ESCROW_AMOUNT,
                "Some Title",
                "http://some.description.link",
                "some-hash-here",
                lambdaObject
            )
        )

    const submissionOp = await proposalSubmission.send()
    await checkConfirmed(config, submissionOp.hash)
    console.log("  - Proposal injected in", submissionOp.hash)

    // Pass the proposal
    console.log("  - Voting yay...")
    const voteOp = await vestingVaultContract.methods.vote(0).send()
    await checkConfirmed(config, voteOp.hash)
    console.log("  - Vote injected in", voteOp.hash)

    // Wait voting to end
    await Utils.sleep((config.GOV_PARAMS.voteLengthBlocks * config.OPERATION_DELAY_SECS) * 1.1)

    console.log("  - Ending vote...")
    const endVotingOp = await dao.methods.endVoting(null).send()
    await checkConfirmed(config, endVotingOp.hash)
    console.log("  - endVoting injected in", endVotingOp.hash)

    // Ensure timelock completed
    await Utils.sleep((config.GOV_PARAMS.blocksInTimelockForExecution * config.OPERATION_DELAY_SECS) * 1.1)

    console.log("  - Executing timelock...")
    const executeTimelockOp = await vestingVaultContract.methods.executeTimelock(null).send()
    console.log("  - Executing timelock injected in", executeTimelockOp.hash)
    await checkConfirmed(config, executeTimelockOp.hash)
}
