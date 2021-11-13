"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeGovProposal = exports.getTokenBalance = exports.getCache = exports.fetchFromCache = exports.fetchOrRun = exports.opHashFromTaquito = exports.transactionIsTransactionResult = exports.objectToMichelson = exports.checkConfirmed = exports.deployContract = exports.sendOperation = exports.initConseil = exports.loadContract = void 0;
const node_fetch_1 = __importDefault(require("node-fetch"));
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
const bignumber_js_1 = require("bignumber.js");
const loglevel_1 = require("loglevel");
const conseiljs_1 = require("conseiljs");
const harbinger_lib_1 = require("@tacoinfra/harbinger-lib");
const compile_break_glass_lambda_1 = require("./utils/compile-break-glass-lambda");
const michel_codec_1 = require("@taquito/michel-codec");
const axios = require('axios').default;
const CACHE_FILE = path_1.default.join(__dirname, '../deploy-data.json');
function loadContract(filename) {
    return fs_1.default.readFileSync(filename).toString();
}
exports.loadContract = loadContract;
function initConseil(conseilLogLevel) {
    const logger = (0, loglevel_1.getLogger)('conseiljs');
    logger.setLevel(conseilLogLevel, false);
    (0, conseiljs_1.registerLogger)(logger);
    (0, conseiljs_1.registerFetch)(node_fetch_1.default);
}
exports.initConseil = initConseil;
async function sendOperation(config, contractAddress, entrypoint, parameter, amount = 0, batch) {
    try {
        console.log(`Using amount: ${amount}`);
        console.log(`Using param: ${parameter}`);
        const Tezos = await config.getTezos();
        const contract = await Tezos.contract.at(contractAddress);
        let invocation;
        if (Array.isArray(parameter)) {
            invocation = contract.methods[entrypoint].apply(null, parameter);
        }
        else if (parameter === null) {
            invocation = contract.methods[entrypoint]();
        }
        else {
            invocation = contract.methods[entrypoint](parameter);
        }
        if (batch !== undefined) {
            batch.withContractCall(invocation);
        }
        else {
            let result;
            if (amount !== 0) {
                result = await invocation.send({ amount, mutez: true });
            }
            else {
                result = await invocation.send();
            }
            console.log(`Deployed in hash: ${result.hash}`);
            console.log('');
            console.log("Awaiting confirmation...");
            await (0, exports.checkConfirmed)(config, result.hash);
            console.log("Confirmed!");
            return result.hash;
        }
    }
    catch (e) {
        console.log('Caught exception, retrying...');
        console.log(e.message);
        console.error(e);
        await harbinger_lib_1.Utils.sleep(config.OPERATION_DELAY_SECS);
        return sendOperation(config, contractAddress, entrypoint, parameter, amount);
    }
}
exports.sendOperation = sendOperation;
async function deployContract(config, contractSource, storage) {
    try {
        console.log(`Using storage: ${storage}`);
        const Tezos = await config.getTezos();
        const result = await Tezos.contract.originate({
            code: contractSource,
            init: storage,
        });
        console.log(`Deployed in hash: ${result.hash}`);
        console.log(`Deployed contract: ${result.contractAddress}`);
        console.log('');
        console.log("Awaiting confirmation...");
        await (0, exports.checkConfirmed)(config, result.hash);
        console.log("Confirmed!");
        return {
            operationHash: result.hash,
            contractAddress: result.contractAddress || "ERR",
        };
    }
    catch (e) {
        console.log('Caught exception, retrying...');
        console.error(e);
        debugger;
        console.log(e.message);
        await harbinger_lib_1.Utils.sleep(config.OPERATION_DELAY_SECS);
        return deployContract(config, contractSource, storage);
    }
}
exports.deployContract = deployContract;
const checkConfirmed = async (config, operationHash) => {
    await harbinger_lib_1.Utils.sleep((config.NUMBER_OF_CONFIRMATIONS) * config.OPERATION_DELAY_SECS);
    const operationStatusUrl = `${config.BETTER_CALL_DEV_BASE_URL}/opg/${operationHash}`;
    const headUrl = `${config.NODE_URL}/chains/main/blocks/head/header`;
    for (let currentTry = 0; currentTry < config.MAX_RETRIES_FOR_CONFIRMATION_POLLING; currentTry++) {
        try {
            const operationDataResult = await axios.get(operationStatusUrl);
            if (operationDataResult.status != 200) {
                throw new Error(`Got status code ${operationDataResult.status} when querying operation status`);
            }
            const operationData = operationDataResult.data[0];
            const headResult = await axios.get(headUrl);
            if (headResult.status != 200) {
                throw new Error(`Got status code ${headResult.status} when querying operation status.`);
            }
            const headData = headResult.data;
            if (operationData.status !== 'applied') {
                throw new Error(`Operation is not applied! Current status: ${operationData.status}`);
            }
            const headLevel = new bignumber_js_1.BigNumber(headData.level);
            const operationLevel = new bignumber_js_1.BigNumber(operationData.level);
            const delta = headLevel.minus(operationLevel);
            if (delta.isLessThan(config.NUMBER_OF_CONFIRMATIONS)) {
                throw new Error(`Did not have required number of confirmations. Head: ${headLevel.toFixed()}, Operation: ${operationLevel.toFixed()}`);
            }
            return;
        }
        catch (e) {
            console.log(`Caught exception while polling ${e}`);
            console.log(`(Try ${currentTry + 1} of ${config.MAX_RETRIES_FOR_CONFIRMATION_POLLING})`);
            await harbinger_lib_1.Utils.sleep(config.OPERATION_DELAY_SECS);
        }
    }
    throw new Error(`Could not confirm operation ${operationHash}`);
};
exports.checkConfirmed = checkConfirmed;
const char2Bytes = (str) => "0x" + Buffer.from(str, "utf8").toString("hex");
function objectToMichelson(obj) {
    const data = [];
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            if (typeof obj[key] !== 'string') {
                throw new Error("Can not serialize anything but string values!");
            }
            if (isNaN(parseInt(key))) {
                data.push(`Elt "${key}" ${char2Bytes(obj[key])}`);
            }
            else {
                data.push(`Elt ${key} ${char2Bytes(obj[key])}`);
            }
        }
    }
    return `{ ${data.join("; ")} }`;
}
exports.objectToMichelson = objectToMichelson;
function transactionIsTransactionResult(tx) {
    return tx.hash !== undefined;
}
exports.transactionIsTransactionResult = transactionIsTransactionResult;
function opHashFromTaquito(input) {
    if (transactionIsTransactionResult(input)) {
        return input.hash;
    }
    else {
        return input.opHash;
    }
}
exports.opHashFromTaquito = opHashFromTaquito;
async function fetchOrRun(key, runFunction) {
    const deployCache = await getCache();
    if (deployCache.hasOwnProperty(key)) {
        console.log(`Loaded '${key}' from the cache!`);
        return deployCache[key];
    }
    else {
        let result = await runFunction();
        if (result === undefined) {
            result = true;
        }
        deployCache[key] = result;
        fs_1.default.writeFileSync(CACHE_FILE, JSON.stringify(deployCache, null, 2));
        return result;
    }
}
exports.fetchOrRun = fetchOrRun;
async function fetchFromCache(key) {
    const deployCache = await getCache();
    if (deployCache.hasOwnProperty(key)) {
        return deployCache[key];
    }
    else {
        throw new Error(`key '${key}' not found in cache`);
    }
}
exports.fetchFromCache = fetchFromCache;
async function getCache() {
    if (!fs_1.default.existsSync(CACHE_FILE)) {
        console.log("Creating a new deploy cache");
        fs_1.default.writeFileSync(CACHE_FILE, JSON.stringify({
            created: new Date()
        }));
    }
    return JSON.parse(fs_1.default.readFileSync(CACHE_FILE).toString());
}
exports.getCache = getCache;
async function getTokenBalance(address, kDAOAddress, config) {
    const tezos = await config.getTezos();
    const tokenContract = await tezos.contract.at(kDAOAddress);
    const tokenStorage = await tokenContract.storage();
    const balance = await tokenStorage.balances.get(address);
    return balance === undefined ? new bignumber_js_1.BigNumber(0) : balance;
}
exports.getTokenBalance = getTokenBalance;
const executeGovProposal = async (vestingVaultContractAddress, breakGlassContract, targetAddress, entryPoint, entryArguments, entryArgumentType, daoAddress, tezos, config) => {
    const vestingVaultContract = await tezos.contract.at(vestingVaultContractAddress);
    let compiledLambda;
    if (breakGlassContract !== null) {
        console.log(`  - Compiling break glass operation...`);
        compiledLambda = (0, compile_break_glass_lambda_1.compileBreakGlassOperation)(targetAddress, entryPoint, entryArguments, entryArgumentType, breakGlassContract);
    }
    else {
        throw new Error("Tried to compile a non-break glass lambda!");
    }
    const michelsonParser = new michel_codec_1.Parser();
    const lambdaObject = michelsonParser.parseMichelineExpression(compiledLambda);
    console.log("  - Submitting proposal...");
    const proposalSubmission = tezos.contract.batch([])
        .withContractCall(vestingVaultContract.methods.propose(config.GOV_PARAMS.escrowAmount, "Some Title", "http://some.description.link", "some-hash-here", lambdaObject));
    const submissionOp = await proposalSubmission.send();
    await (0, exports.checkConfirmed)(config, submissionOp.hash);
    console.log("  - Proposal injected in", submissionOp.hash);
    console.log("  - Voting yay...");
    const voteOp = await vestingVaultContract.methods.vote(0).send();
    await (0, exports.checkConfirmed)(config, voteOp.hash);
    console.log("  - Vote injected in", voteOp.hash);
    await harbinger_lib_1.Utils.sleep((config.GOV_PARAMS.voteLengthBlocks * config.OPERATION_DELAY_SECS) * 1.1);
    console.log("  - Ending vote...");
    const dao = await tezos.contract.at(daoAddress);
    const endVotingOp = await dao.methods.endVoting(null).send();
    await (0, exports.checkConfirmed)(config, endVotingOp.hash);
    console.log("  - endVoting injected in", endVotingOp.hash);
    await harbinger_lib_1.Utils.sleep((config.GOV_PARAMS.blocksInTimelockForExecution * config.OPERATION_DELAY_SECS) * 1.1);
    console.log("  - Executing timelock...");
    const executeTimelockOp = await vestingVaultContract.methods.executeTimelock(null).send();
    console.log("  - Executing timelock injected in", executeTimelockOp.hash);
    await (0, exports.checkConfirmed)(config, executeTimelockOp.hash);
};
exports.executeGovProposal = executeGovProposal;
//# sourceMappingURL=utils.js.map