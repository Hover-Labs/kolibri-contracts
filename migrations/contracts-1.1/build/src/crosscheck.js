"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("./utils");
const harbinger_lib_1 = require("@tacoinfra/harbinger-lib");
async function crosscheck(config) {
    console.log('>>> [1/4] Input params:');
    console.log(`Tezos Node: ${config.NODE_URL}`);
    console.log(`Indexer URL: ${config.BETTER_CALL_DEV_BASE_URL}`);
    console.log('');
    console.log(`>>> [2/4] Initializing Conseil with logging level: ${config.LOG_LEVEL}`);
    (0, utils_1.initConseil)(config.LOG_LEVEL);
    (0, harbinger_lib_1.initOracleLib)(config.LOG_LEVEL);
    console.log('Conseil initialized.');
    console.log('');
    console.log('>>> [3/4] Initializing Deployer');
    const keystore = await harbinger_lib_1.Utils.keyStoreFromPrivateKey(config.privateKey);
    await harbinger_lib_1.Utils.revealAccountIfNeeded(config.NODE_URL, keystore, await harbinger_lib_1.Utils.signerFromKeyStore(keystore));
    console.log(`Initialized deployer: ${keystore.publicKeyHash}`);
    console.log('');
    console.log('>>> [4/4] Loading contracts...');
    const contractSources = {
        newMinterContractSource: (0, utils_1.loadContract)(`${__dirname}/../../../smart_contracts/minter.tz`),
        breakGlassContractSource: (0, utils_1.loadContract)(`${__dirname}/../../../break-glass-contracts/smart_contracts/break-glass.tz`)
    };
    console.log('Contracts loaded.');
    console.log('');
    console.log('------------------------------------------------------');
    console.log('>> Crosscheck complete. Flight attendants take your jump seats.');
    console.log('>> Deploying Core contracts... ');
    console.log('------------------------------------------------------');
    console.log('');
    return {
        keystore,
        contractSources
    };
}
exports.default = crosscheck;
//# sourceMappingURL=crosscheck.js.map