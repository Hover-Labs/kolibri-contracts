"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
    result["default"] = mod;
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const jsonpath_plus_1 = require("jsonpath-plus");
const TezosTypes = __importStar(require("../../../types/tezos/TezosChainTypes"));
const TezosMessageUtil_1 = require("../TezosMessageUtil");
const TezosNodeReader_1 = require("../TezosNodeReader");
const TezosNodeWriter_1 = require("../TezosNodeWriter");
const TezosContractUtils_1 = require("./TezosContractUtils");
var StakerDAOTokenHelper;
(function (StakerDAOTokenHelper) {
    function verifyDestination(server, address) {
        return __awaiter(this, void 0, void 0, function* () {
            return TezosContractUtils_1.TezosContractUtils.verifyDestination(server, address, '0e3e137841a959521324b4ce20ca2df7');
        });
    }
    StakerDAOTokenHelper.verifyDestination = verifyDestination;
    function verifyScript(script) {
        return TezosContractUtils_1.TezosContractUtils.verifyScript(script, 'b77ada691b1d630622bea243696c84d7');
    }
    StakerDAOTokenHelper.verifyScript = verifyScript;
    function getAccountBalance(server, mapid, account) {
        return __awaiter(this, void 0, void 0, function* () {
            const packedKey = TezosMessageUtil_1.TezosMessageUtils.encodeBigMapKey(Buffer.from(TezosMessageUtil_1.TezosMessageUtils.writePackedData(account, 'address'), 'hex'));
            const mapResult = yield TezosNodeReader_1.TezosNodeReader.getValueForBigMapKey(server, mapid, packedKey);
            if (mapResult === undefined) {
                throw new Error(`Map ${mapid} does not contain a record for ${account}`);
            }
            return Number(jsonpath_plus_1.JSONPath({ path: '$.int', json: mapResult })[0]);
        });
    }
    StakerDAOTokenHelper.getAccountBalance = getAccountBalance;
    function getSimpleStorage(server, address) {
        return __awaiter(this, void 0, void 0, function* () {
            const storageResult = yield TezosNodeReader_1.TezosNodeReader.getContractStorage(server, address);
            return {
                mapid: Number(jsonpath_plus_1.JSONPath({ path: '$.args[1].args[1].args[0].int', json: storageResult })[0]),
                council: jsonpath_plus_1.JSONPath({ path: '$.args[0].args[0].args[1]..string', json: storageResult }),
                stage: Number(jsonpath_plus_1.JSONPath({ path: '$.args[1].args[0].args[0].int', json: storageResult })[0]),
                phase: Number(jsonpath_plus_1.JSONPath({ path: '$.args[1].args[0].args[0].int', json: storageResult })[0]) % 4,
                supply: Number(jsonpath_plus_1.JSONPath({ path: '$.args[1].args[0].args[1].int', json: storageResult })[0]),
                paused: (jsonpath_plus_1.JSONPath({ path: '$.args[1].args[1].args[1].args[0].prim', json: storageResult })[0]).toString().toLowerCase().startsWith('t')
            };
        });
    }
    StakerDAOTokenHelper.getSimpleStorage = getSimpleStorage;
    function transferBalance(server, signer, keystore, contract, fee, source, destination, amount, gas, freight) {
        return __awaiter(this, void 0, void 0, function* () {
            const parameters = `(Right (Left (Left (Right (Pair "${source}" (Pair "${destination}" ${amount}))))))`;
            const nodeResult = yield TezosNodeWriter_1.TezosNodeWriter.sendContractInvocationOperation(server, signer, keystore, contract, 0, fee, freight, gas, '', parameters, TezosTypes.TezosParameterFormat.Michelson);
            return TezosContractUtils_1.TezosContractUtils.clearRPCOperationGroupHash(nodeResult.operationGroupID);
        });
    }
    StakerDAOTokenHelper.transferBalance = transferBalance;
})(StakerDAOTokenHelper = exports.StakerDAOTokenHelper || (exports.StakerDAOTokenHelper = {}));
//# sourceMappingURL=StakerDAOTokenHelper.js.map