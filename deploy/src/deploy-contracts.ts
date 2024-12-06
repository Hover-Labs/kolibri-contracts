import {
  initConseil,
  loadContract,
  deployContract,
  sendOperation,
} from './utils'
import { initOracleLib, Utils } from '@tacoinfra/harbinger-lib'
import { TezosNodeReader } from 'conseiljs'

// How long to wait after an operation broadcast to move on.
// Blocks on mainnet are 60s, blocks on testnet are 30s. Prefer at least 2 blocks in case of a priority 1 bake.
export const OPERATION_DELAY_SECS = 10

//-------------------------------------------------------------------
// DEPLOYMENT PARAMETERS
//-------------------------------------------------------------------

// Whether to use testnet or or mainnet configurations.
const IS_MAINNET = false

// Tezos node address.
const NODE_ADDRESS = IS_MAINNET
  ? 'https://rpc.tzbeta.net'
  : 'https://rpczero.tzbeta.net'

// Initial collateralization ratio. Specified in 6 digits. Ex. 2_000_000 = 2 XTZ / USD for each kUSD.
const COLLATERALIZATION_RATIO = '200000000000000000000' // 200%

// Harbinger Normalizer Contract to call on.
const HARBINGER_NORMALIZER = IS_MAINNET
  ? 'KT1AdbYiPYb5hDuEuVrfxmFehtnBCXv4Np7r'
  : 'KT1SUP27JhX24Kvr11oUdWswk7FnCW78ZyUn'

// UBINETIC On-Demand Proxy Contract to call on.
const UBINETIC_ON_DEMAND_PROXY = IS_MAINNET
  ? 'KT1B74ywpG3nX2F3ZgpYi4MnsyuoYyQtQTAn'
  : null // FIXME: No contract in ghostnet

// Key which will deploy the contracts.
const DEPLOYER_PRIVATE_KEY =
  'edsk3aeocSRnxdWVFm3ShaALUeCTy4PgL6JdeGvzbLjX5jn8D9ZXw5'

// Log level to use for Conseil.
const CONSEIL_LOG_LEVEL = 'error' // Valid options: 'error' | 'debug'

// Initial debt ceiling.
const DEBT_CEILING = '1000' // $1000

// The maximum delay for data from Harbinger, in seconds.
const MAX_DATA_DELAY_SECS = 30 * 60 // 30 min

// The liquidation fee.
const LIQUIDATION_FEE = '80000000000000000' // 8%

// The maximum value allowed in an oven.
// Valid Values: `Some <Value> or `None`
const INITIAL_OVEN_MAX_MUTEZ = 'Some 100000000' // 100 XTZ

// The percent of fees to give to the Dev fund
const DEV_FUND_SPLIT = '100000000000000000' // 10%

// The stability fee to apply per period.
const STABILITY_FEE = 0 // 0%

// Initial oven baker.
// Valid values: `Some <addr>` or `None`
const INITIAL_OVEN_BAKER = 'None'

//-------------------------------------------------------------------
// PROGRAM
//-------------------------------------------------------------------

const currentDate = new Date()
const timestampMs = currentDate.getTime()
const timestampSec = Math.floor(timestampMs / 1000)

async function main() {
  console.log('------------------------------------------------------')
  console.log('> Deploying Kolibri Infrastructure')
  console.log('>> Running Pre Flight Checks...')
  console.log('------------------------------------------------------')

  console.log('>>> [1/5] Input params:')
  console.log(`Tezos Node: ${NODE_ADDRESS}`)
  console.log(`Initial Collateralization Ratio: ${COLLATERALIZATION_RATIO}`)
  console.log(`Initial time: ${timestampSec}`)
  console.log('')

  console.log(
    `>>> [2/5] Initializing Conseil with logging level: ${CONSEIL_LOG_LEVEL}`,
  )
  initConseil(CONSEIL_LOG_LEVEL)
  initOracleLib(CONSEIL_LOG_LEVEL)
  console.log('Conseil initialized.')
  console.log('')

  console.log('>>> [3/5] Initializing Deployer')
  const keystore = await Utils.keyStoreFromPrivateKey(DEPLOYER_PRIVATE_KEY)
  await Utils.revealAccountIfNeeded(
    NODE_ADDRESS,
    keystore,
    await Utils.signerFromKeyStore(keystore),
  )
  console.log(`Initialized deployer: ${keystore.publicKeyHash}`)
  console.log('')

  console.log('>>> [4/5] Loading contracts...')
  const tokenContractSource = loadContract(
    `${__dirname}/../../smart_contracts/token.tz`,
  )
  const minterContractSource = loadContract(
    `${__dirname}/../../smart_contracts/minter.tz`,
  )
  const ovenProxyContractSource = loadContract(
    `${__dirname}/../../smart_contracts/oven-proxy.tz`,
  )
  const ovenRegistryContractSource = loadContract(
    `${__dirname}/../../smart_contracts/oven-registry.tz`,
  )
  const ovenFactoryContractSource = loadContract(
    `${__dirname}/../../smart_contracts/oven-factory.tz`,
  )
  const devFundContractSource = loadContract(
    `${__dirname}/../../smart_contracts/dev-fund.tz`,
  )
  const stabilityFundContractSource = loadContract(
    `${__dirname}/../../smart_contracts/stability-fund.tz`,
  )
  const oracleSource = loadContract(
    `${__dirname}/../../smart_contracts/oracle.tz`,
  )
  const oracleOnDemandSource = loadContract(
    `${__dirname}/../../smart_contracts/oracle-on-demand.tz`,
  )
  console.log('Contracts loaded.')
  console.log('')

  console.log('>>> [5/5] Getting Account Counter')
  let counter = await TezosNodeReader.getCounterForAccount(
    NODE_ADDRESS,
    keystore.publicKeyHash,
  )
  console.log(`Got counter: ${counter}`)
  console.log('')

  console.log('------------------------------------------------------')
  console.log('>> Preflight Checks Passed!')
  console.log('>> Deploying Contracts...')
  console.log('------------------------------------------------------')
  console.log('')

  console.log('>>> [1/9] Deploying Minter Contract...')
  // Constants:
  // Interest Index: 1000000000000000000 (1)
  const minterContractStorage = `(Pair (Pair (Pair ${COLLATERALIZATION_RATIO} (Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}")) (Pair 1000000000000000000 (Pair "${timestampSec}" ${LIQUIDATION_FEE}))) (Pair (Pair (${INITIAL_OVEN_MAX_MUTEZ}) (Pair "${keystore.publicKeyHash}" ${DEV_FUND_SPLIT})) (Pair ${STABILITY_FEE} (Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}"))))`
  counter++
  const minterContractDeployResult = await deployContract(
    minterContractSource,
    minterContractStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [2/9] Deploying Oven Proxy Contract...')
  // Constants:
  // state: 0 (IDLE)
  const ovenProxyStorage = `(Pair (Pair (Pair None "${keystore.publicKeyHash}") (Pair None (Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}"))) (Pair (Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}") (Pair False (Pair 0 None))))`
  counter++
  const ovenProxyDeployResult = await deployContract(
    ovenProxyContractSource,
    ovenProxyStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [3/9] Deploying Oven Factory Contract...')
  // Constants:
  // makeOvenOwner: None
  // state: 0 (IDLE)
  const ovenFactoryStorage = `(Pair (Pair "${keystore.publicKeyHash}" (Pair (${INITIAL_OVEN_BAKER}) None)) (Pair (Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}") (Pair "${keystore.publicKeyHash}" 0)))`
  counter++
  const ovenFactoryDeployResult = await deployContract(
    ovenFactoryContractSource,
    ovenFactoryStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [4/9] Deploying Token Contract...')
  // Constants:
  // Balances: {} (No initial balances)
  // Metadata: {} (No initial metadata)
  // Paused: False
  const tokenContractStorage = `(Pair (Pair (Pair "${keystore.publicKeyHash}" {}) (Pair ${DEBT_CEILING} "${keystore.publicKeyHash}")) (Pair (Pair {Elt "" 0x74657a6f732d73746f726167653a64617461; Elt "data" 0x7b20226e616d65223a20224b6f6c6962726920546f6b656e20436f6e7472616374222c20226465736372697074696f6e223a20224641312e3220496d706c656d656e746174696f6e206f66206b555344222c2022617574686f72223a2022486f766572204c616273222c2022686f6d6570616765223a20202268747470733a2f2f6b6f6c696272692e66696e616e6365222c2022696e7465726661636573223a205b2022545a49502d3030372d323032312d30312d3239225d207d} False) (Pair {Elt 0 (Pair 0 {Elt "decimals" 0x3138; Elt "icon" 0x2068747470733a2f2f6b6f6c696272692d646174612e73332e616d617a6f6e6177732e636f6d2f6c6f676f2e706e67; Elt "name" 0x4b6f6c6962726920555344; Elt "symbol" 0x6b555344})} 0)))`
  counter++
  const tokenContractDeployResult = await deployContract(
    tokenContractSource,
    tokenContractStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [5/9] Deploying Oven Registry Contract...')
  // Constants:
  // OvenMap: {} (No initial ovens)
  const ovenRegistryStorage = `(Pair "${keystore.publicKeyHash}"(Pair "${keystore.publicKeyHash}" {}))`
  counter++
  const ovenRegistryDeployResult = await deployContract(
    ovenRegistryContractSource,
    ovenRegistryStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [6/9] Deploying Dev Fund Contract...')
  const devFundStorage = `(Pair "${keystore.publicKeyHash}"(Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}"))`
  counter++
  const devFundDeployResult = await deployContract(
    devFundContractSource,
    devFundStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [7/9] Deploying Stability Fund Contract...')
  const stabilityFundStorage = `(Pair(Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}")(Pair "${keystore.publicKeyHash}" "${keystore.publicKeyHash}"))`
  counter++
  const stabilityFundDeployResult = await deployContract(
    stabilityFundContractSource,
    stabilityFundStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  // FIXME: Outdated oracle
  // console.log('>>> [8/9] Deploying Oracle Contract...')
  // // Constants:
  // // clientCallback: None
  // // state: 0 (IDLE)
  // const oracleStorage = `(Pair(Pair None "${keystore.publicKeyHash}")(Pair "${HARBINGER_NORMALIZER}"(Pair ${MAX_DATA_DELAY_SECS} 0)))`
  // counter++
  // const oracleDeployResult = await deployContract(
  //   oracleSource,
  //   oracleStorage,
  //   keystore,
  //   counter,
  //   NODE_ADDRESS,
  // )
  // console.log('Deployed.')
  // console.log('')

  console.log('>>> [8/9] Deploying Oracle Contract...')
  // TODO: Check if this format is correct
  // Alt format will be: 
  // `(Pair "${UBINETIC_ON_DEMAND_PROXY}" ${MAX_DATA_DELAY_SECS} "${keystore.publicKeyHash}")`
  const oracleStorage = `(Pair "${UBINETIC_ON_DEMAND_PROXY}" (Pair ${MAX_DATA_DELAY_SECS} "${keystore.publicKeyHash}"))`
  counter++
  const oracleDeployResult = await deployContract(
    oracleSource,
    oracleStorage,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Deployed.')
  console.log('')

  console.log('>>> [9/9] Finishing up...')
  console.log(
    `Waiting ${OPERATION_DELAY_SECS} seconds for operations to settle in blocks...`,
  )
  await Utils.sleep(OPERATION_DELAY_SECS)
  console.log('Onwards!')
  console.log('')

  console.log('------------------------------------------------------')
  console.log('>> Contracts Deployed!')
  console.log('>> Wiring contracts to each other...')
  console.log('------------------------------------------------------')
  console.log('')

  // Oven Proxy
  console.log('>>> [1/11] Setting Oven Proxy to point to minter.')
  counter++
  await sendOperation(
    ovenProxyDeployResult.contractAddress,
    'setMinterContract',
    `"${minterContractDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )

  console.log('Done.')
  console.log('')

  console.log('>>> [2/11] Setting Oven Proxy to point to oven registry.')
  counter++
  await sendOperation(
    ovenProxyDeployResult.contractAddress,
    'setOvenRegistryContract',
    `"${ovenRegistryDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  console.log('>>> [3/11] Setting Oven Proxy to point to oven registry.')
  counter++
  await sendOperation(
    ovenProxyDeployResult.contractAddress,
    'setOracleContract',
    `"${oracleDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  // Minter
  console.log('>>> [4/11] Setting Minter to use Contracts')
  counter++
  const minterParam = `(Pair "${keystore.publicKeyHash}"(Pair "${tokenContractDeployResult.contractAddress}"(Pair "${ovenProxyDeployResult.contractAddress}"(Pair "${stabilityFundDeployResult.contractAddress}" "${devFundDeployResult.contractAddress}"))))`
  console.log(`Minter param: ${minterParam} `)
  await sendOperation(
    minterContractDeployResult.contractAddress,
    'updateContracts',
    minterParam,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  // Token Contract
  console.log('>>> [5/11] Setting Token Contract to use Minter as Admin')
  counter++
  await sendOperation(
    tokenContractDeployResult.contractAddress,
    'setAdministrator',
    `"${minterContractDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  // Oven Factory
  console.log('>>> [6/11] Setting Oven Factory Contract to use Oven Registry')
  counter++
  await sendOperation(
    ovenFactoryDeployResult.contractAddress,
    'setOvenRegistryContract',
    `"${ovenRegistryDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  console.log('>>> [7/11] Setting Oven Factory Contract to use Minter')
  counter++
  await sendOperation(
    ovenFactoryDeployResult.contractAddress,
    'setMinterContract',
    `"${minterContractDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  console.log('>>> [8/11] Setting Oven Factory Contract to use Oven Proxy')
  counter++
  await sendOperation(
    ovenFactoryDeployResult.contractAddress,
    'setOvenProxyContract',
    `"${ovenProxyDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  // Oven Registry
  console.log('>>> [9/11] Setting Oven Registry Contract to use Oven Factory')
  counter++
  await sendOperation(
    ovenRegistryDeployResult.contractAddress,
    'setOvenFactoryContract',
    `"${ovenFactoryDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  // Stability Fund
  console.log('>>> [10/11] Setting Stability Fund to use Oven Registry')
  counter++
  await sendOperation(
    stabilityFundDeployResult.contractAddress,
    'setOvenRegistryContract',
    `"${ovenRegistryDeployResult.contractAddress}"`,
    keystore,
    counter,
    NODE_ADDRESS,
  )
  console.log('Done.')
  console.log('')

  console.log('>>> [11/11] Finishing up...')
  console.log(
    `Waiting ${OPERATION_DELAY_SECS} seconds for operations to settle in blocks...`,
  )
  await Utils.sleep(OPERATION_DELAY_SECS)
  console.log('Onwards!')
  console.log('')

  console.log('------------------------------------------------------')
  console.log('>> Multisig Setup Done!')
  console.log('> All Done!')
  console.log('------------------------------------------------------')
  console.log('')

  console.log(
    `Minter Contract:                   ${minterContractDeployResult.contractAddress} / ${minterContractDeployResult.operationHash}`,
  )
  console.log(
    `Oven Proxy Contract:               ${ovenProxyDeployResult.contractAddress} / ${ovenProxyDeployResult.operationHash}`,
  )
  console.log(
    `Oven Factory Contract:             ${ovenFactoryDeployResult.contractAddress} / ${ovenFactoryDeployResult.operationHash}`,
  )
  console.log(
    `Token Contract:                    ${tokenContractDeployResult.contractAddress} / ${tokenContractDeployResult.operationHash}`,
  )
  console.log(
    `Oven Registry Contract:            ${ovenRegistryDeployResult.contractAddress} / ${ovenRegistryDeployResult.operationHash}`,
  )
  console.log(
    `Dev Fund Contract:                 ${devFundDeployResult.contractAddress} / ${devFundDeployResult.operationHash}`,
  )
  console.log(
    `Stability Fund Contract:           ${stabilityFundDeployResult.contractAddress} / ${stabilityFundDeployResult.operationHash}`,
  )
  console.log(
    `Oracle Contract:                   ${oracleDeployResult.contractAddress} / ${oracleDeployResult.operationHash}`,
  )
}

void main()
