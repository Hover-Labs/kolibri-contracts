import { loadContract } from "./utils";
// import { initOracleLib, Utils } from "@tacoinfra/harbinger-lib";
import { KeyStore } from "conseiljs";

type CrossCheckResult = {
    // keystore: KeyStore,
    contractSources: any
}

export default async function crosscheck(config: any): Promise<CrossCheckResult> {
    console.log('>>> [1/4] Input params:')
    console.log('')

    // console.log(`>>> [2/4] Initializing Conseil with logging level: ${config.LOG_LEVEL}`)
    // initConseil(config.LOG_LEVEL)
    // initOracleLib(config.LOG_LEVEL)
    // console.log('Conseil initialized.')
    // console.log('')

    // console.log('>>> [3/4] Initializing Deployer')
    // const keystore = await Utils.keyStoreFromPrivateKey(config.privateKey)
    // await Utils.revealAccountIfNeeded(
    //     config.NODE_URL,
    //     keystore,
    //     await Utils.signerFromKeyStore(keystore),
    // )
    // console.log(`Initialized deployer: ${keystore.publicKeyHash}`)
    // console.log('')

    console.log('>>> [4/4] Loading contracts...')

    const contractSources = {
        newMinterContractSource: loadContract(`${__dirname}/../../../smart_contracts/minter.tz`),
        breakGlassContractSource: loadContract(`${__dirname}/../../../break-glass-contracts/smart_contracts/break-glass.tz`)
    }

    console.log('Contracts loaded.')
    console.log('')

    console.log('------------------------------------------------------')
    console.log('>> Crosscheck complete. Flight attendants take your jump seats.')
    console.log('>> Deploying Core contracts... ')
    console.log('------------------------------------------------------')
    console.log('')

    return {
        // keystore,
        contractSources
    }
}
