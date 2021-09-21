import Network from './network'
import Address from './types/address'
import OperationHash from './types/operation-hash'
import { ThanosWallet } from '@thanos-wallet/dapp'
import { InMemorySigner } from '@taquito/signer'
import Shard from './types/shard'
import Mutez from './types/mutez'
import { TezosToolkit, TransactionWalletOperation } from '@taquito/taquito'
import { TransactionOperation } from '@taquito/taquito/dist/types/operations/transaction-operation'
import BigNumber from 'bignumber.js'
import axios, { AxiosResponse } from 'axios'

/** The number of seconds in a compound interest period */
const COMPOUND_PERIOD_SECONDS = 60

/** The number of periods that occur per year. */
const COMPOUNDS_PER_YEAR = (365 * 24 * 60 * 60) / COMPOUND_PERIOD_SECONDS // (Number of seconds in year) / (seconds per compound)

/** The number of decimals in smart contract precision */
// TODO(keefertaylor): Refactor to a constant.
const PRECISION = new BigNumber(Math.pow(10, 18))

/** The result of deploying an Oven. */
export type OvenDeployResult = {
  // The operation hash.
  operationHash: OperationHash

  // The Oven's address
  ovenAddress: Address
}

/** A model object for an oven. */
export type Oven = {
  // The oven's owner
  ovenOwner: Address

  // The address of the oven
  ovenAddress: Address
}

/** A model to use for system interest. */
export type InterestData = {
  // The global interest index.
  globalInterestIndex: Shard

  // The last interest update time
  lastUpdateTime: Date
}

/**
 * Controls interaction and data fetching from the Untitled StableCoin System.
 */
export default class StableCoinClient {
  /** A TezosToolkit */
  private readonly tezos: TezosToolkit

  /**
   * Create a new StableCoinClient.
   *
   * TODO(keefertaylor): Consider fetching references to contracts in this constructor to avoid
   * duplicate network requests later.
   *
   * @param nodeUrl The URL of the node to connect to.
   * @param network The Network the Node is connected to.
   * @param ovenRegistryAddress The address of the OvenRegistry
   * @param minterAddress The address of the Minter.
   * @param ovenFactoryAddress The address of the OvenFactory.
   * @param indexerURL An indexer url to use for querying all ovens. Must be BCD compatible
   */
  public constructor(
    nodeUrl: string,
    private readonly network: Network,
    private readonly ovenRegistryAddress: Address,
    private readonly minterAddress: Address,
    private readonly ovenFactoryAddress: Address,
    private readonly indexerURL?: string,
  ) {
    this.tezos = new TezosToolkit(nodeUrl)
  }

  /**
   * Return the network as a string.
   */
  public getNetwork(): string {
    const networkString = this.network.toString()
    return networkString.charAt(0).toUpperCase() + networkString.slice(1)
  }

  /**
   * Deploy a new Oven.
   *
   * @param wallet The wallet which will deploy the Oven.
   * @returns The result of deploying a new Oven.
   */
  public async deployOven(
    wallet: InMemorySigner | ThanosWallet,
  ): Promise<TransactionWalletOperation | TransactionOperation> {
    if (wallet instanceof InMemorySigner) {
      // Wallet is InMemorySigner
      this.tezos.setProvider({ signer: wallet })
    } else {
      // Wallet is Thanos Wallet
      this.tezos.setWalletProvider(wallet)
    }

    // Invoke contract.
    const ovenFactoryContract = await this.tezos.wallet.at(this.ovenFactoryAddress)

    return ovenFactoryContract.methods.makeOven([['unit']]).send()
  }

  /**
   * Retrieve the stability fee.
   *
   * This returns the stability fee as an APY. Note that internally, linear approximation is used,
   * so this number is not always accurate. See stablecoin documentation.
   *
   * @returns A number representing a percentage fee with 18 decimals of precision.
   */
  public async getStabilityFeeApy(): Promise<Shard> {
    const minterContract = await this.tezos.contract.at(this.minterAddress)
    const minterStorage: any = await minterContract.storage()
    const stabilityFee = await minterStorage.stabilityFee

    const one = new BigNumber(1_000_000_000_000_000_000)
    const initial = stabilityFee.plus(one)
    let apy = one
    for (let n = 0; n < COMPOUNDS_PER_YEAR; n++) {
      apy = apy.times(initial).dividedBy(one)
    }
    return apy.minus(one)
  }

  /**
   * Retrieve the simple stability fee.
   *
   * This interest rate is the interest rate applied per period, *NOT* the APY. Please use `getStabilityFeeApy`
   * instead.
   *
   * @returns A number representing the stability fee per period.
   */
  public async getSimpleStabilityFee(): Promise<Shard> {
    const minterContract = await this.tezos.contract.at(this.minterAddress)
    const minterStorage: any = await minterContract.storage()
    return await minterStorage.stabilityFee
  }

  /**
   * Retrieve the maximum value for an oven.
   *
   * This method returns a Mutez amount if limits are active, otherwise it returns `null`.
   *
   * @returns A number representing the maximum mutez an oven can contain, or `null`.
   */
  public async getMaximumOvenValue(): Promise<Mutez | null> {
    const minterContract = await this.tezos.contract.at(this.minterAddress)
    const minterStorage: any = await minterContract.storage()
    return await minterStorage.ovenMax
  }

  /**
   * Retrieve the collateralization rate.
   *
   * @returns A number representing the required collateralization fee with 18 digits of precision.
   */
  public async getRequiredCollateralizationRatio(): Promise<Shard> {
    const minterContract = await this.tezos.contract.at(this.minterAddress)
    const minterStorage: any = await minterContract.storage()
    return await minterStorage.collateralizationPercentage
  }

  /**
   * Retrieve information about the interest rates in the system.
   *
   * @param time The time to calculate the values at. Defaults to the current time.
   * @returns Interest rate data for the system.
   */
  public async getInterestData(time: Date = new Date()): Promise<InterestData> {
    const minterContract = await this.tezos.contract.at(this.minterAddress)
    const minterStorage: any = await minterContract.storage()

    const globalInterestIndex: BigNumber = await minterStorage.interestIndex

    const raw = await minterStorage.lastInterestIndexUpdateTime
    const lastUpdateTime = new Date(`${raw}`)

    const deltaMs = time.getTime() - lastUpdateTime.getTime()
    const deltaSecs = Math.floor(deltaMs / 1000)
    const numPeriods = Math.floor(deltaSecs / COMPOUND_PERIOD_SECONDS)

    const simpleStabilityFee = await this.getSimpleStabilityFee()

    const globalInterestIndexApproximation = globalInterestIndex
      .times(PRECISION.plus(simpleStabilityFee.times(numPeriods)))
      .div(PRECISION)
    return {
      globalInterestIndex: globalInterestIndexApproximation,
      lastUpdateTime: time,
    }
  }

  /**
   * Retrieve the number of ovens in the system.
   *
   * @returns The number of ovens in the system.
   */
  public async getOvenCount(): Promise<number> {
    const ovens = await this.getAllOvens()
    return ovens.length
  }

  /**
   * Retrieve an array of ovens owned by an address.
   *
   * @param address The address to find Ovens owned by.
   * @returns A list of Addresses of owned ovens.
   */
  public async ovensOwnedByAddress(address: Address): Promise<Array<Address>> {
    const allOvens = await this.getAllOvens()

    return allOvens
      .filter((oven) => {
        return oven.ovenOwner === address
      })
      .map((oven) => {
        return oven.ovenAddress
      })
  }

  /**
   * Retrieve data about all ovens.
   *
   * @returns A list of all known ovens.
   */
  async getAllOvens(): Promise<Array<Oven>> {
    if (this.indexerURL === undefined) {
      const response = await axios.get(`https://kolibri-data.s3.amazonaws.com/${this.network}/oven-key-data.json`)
      return response.data.ovenData
    } else {
      const ovenRegistryContract = await this.tezos.contract.at(this.ovenRegistryAddress)
      const ovenRegistryStorage: any = await ovenRegistryContract.storage()
      const ovenRegistryBigMapId = await ovenRegistryStorage.ovenMap

      let offset = 0

      const results: any[] = []

      // Go paginate on the indexer URL 10 entries at a time
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const values: AxiosResponse = await axios.get(
          `${this.indexerURL}/v1/bigmap/sandboxnet/${ovenRegistryBigMapId}/keys?size=10&offset=${offset}`,
        )
        values.data.forEach((value: any) => {
          results.push({
            ovenAddress: value.data.key.value,
            ovenOwner: value.data.value.value,
          })
        })

        if (values.data.length < 10) {
          break
        }

        offset += 10
      }

      return results
    }
  }
}
