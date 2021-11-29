import BigNumber from 'bignumber.js'
import { CONSTANTS, NetworkConfig, sleep } from '@hover-labs/tezos-utils'
import axios from 'axios'
import { NETWORK_CONFIG } from '../config'
import { TezosToolkit } from '@taquito/taquito'

/** API Responses */
// Response from Oven Indexer API
type OvenDataResponse = {
  ovenData: Array<Oven>
}
type Oven = {
  ovenAddress: string,
  ovenOwner: string
}

// Response from Tezos node for head block
type HeadResponse = {
  header: Header
}
type Header = {
  level: number
}

// TODO(keefertaylor): We should probably just pass through a block nubmer
/** Totals the ovens and returns the result. If this file is run directly, it will output the result. */
export const getTotalAmountLoanded = async (networkConfig: NetworkConfig): Promise<BigNumber> => {
  console.log(`...Performing Pre Flight Checks`)
  const tezos = new TezosToolkit(networkConfig.tezosNodeUrl)
  console.log(`...Cleared for takeoff!`)

  // Sleep for a bit to make sure that the indexer is caught up.
  // TODO(keefertaylor): Enable me.
  const minutesToSleep = 5
  console.log(`...Sleeping for ${minutesToSleep} to make sure the indexer is caught up...`)
  // await sleep(minutesToSleep * 60) // 5 min
  console.log(`...Good morning!`)

  // Query the API for oven Data
  // TODO(keefertaylor): Fix this URL.
  console.log("...Querying for all ovens")
  const ovenApiUrl = `https://kolibri-data.s3.amazonaws.com/mainnet/oven-key-data.json`
  const ovenData: OvenDataResponse = (await axios.get(ovenApiUrl)).data
  const ovens = ovenData.ovenData

  // Get the block from head.
  console.log(`...Querying the current block on ${networkConfig.tezosNodeUrl}`)
  const headUrl = `${networkConfig.tezosNodeUrl}/chains/main/blocks/head/`
  const headData: HeadResponse = (await axios.get(headUrl)).data
  const blockLevel = headData.header.level
  console.log(`...Running calculation at block ${blockLevel}`)

  // Map Each oven to a balance, including interest up to blockLevel
  console.log(`...Resolving data for ${ovens.length} ovens. This also might take some time...`)
  const ovenBalancePromises: Array<Promise<BigNumber>> = ovens.map((oven: Oven, index: number) => {
    return resolveOvenBalanceAtCurrentTime(oven.ovenAddress, blockLevel, tezos)
  })

  // Wait for all Promises to settle
  const ovenBalances: Array<BigNumber> = await Promise.all(ovenBalancePromises)
  console.log("...Resolved balances for all ovens")

  // Sum all the balances together.
  console.log("...Summing all oven values")
  const sum: BigNumber = ovenBalances.reduce((previous: BigNumber, next: BigNumber) => {
    return previous.plus(next)
  }, new BigNumber(0))
  console.log("...Done!")

  return sum
}


/**
 * Given an oven address and a block level, retrieve data about the amounts loaned.
 * 
 * @param ovenAddress The address of the oven to resolve
 * @param blockLevel The block level to pull values at
 * @param tezos A tezos toolkit instance that can talk to the node.
 * @returns The amount of kUSD owed by the oven, as of blockLevel.
 */
const resolveOvenBalanceAtCurrentTime = async (
  ovenAddress: string,
  blockLevel: number,
  tezos: TezosToolkit
): Promise<BigNumber> => {
  const ovenContract = await tezos.contract.at(ovenAddress)
  const ovenStorage: any = await ovenContract.storage()

  // TODO(keefertaylor): Implement me when Taquito supports on chain views.
  return Promise.resolve(new BigNumber(1))
}

const main = async () => {
  BigNumber.config({ ROUNDING_MODE: BigNumber.ROUND_DOWN })

  console.log("Totaling all outstanding value. This might take a few minutes...")
  const totalAmountLoaned = await getTotalAmountLoanded(NETWORK_CONFIG)
  console.log("")

  console.log("The total amount is:")
  console.log(totalAmountLoaned.dividedBy(CONSTANTS.MANTISSA).toFixed(18))
  console.log("")

  console.log("The value to be submitted to the minter initializer is:")
  console.log(totalAmountLoaned.toFixed())
  console.log("")
}

// If called directly
if (require.main === module) {
  (async () => {
    try {
      console.log(await main())
    } catch (e) {
      console.error(e)
      debugger;
    }
  })()
}