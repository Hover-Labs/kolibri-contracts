import Address from './types/address'
import { TezosToolkit } from '@taquito/taquito'
import Mutez from './types/mutez'

/** Asset pair to query */
const ASSET_CODE = 'XTZ-USD'

/**
 * Price feed data.
 */
export type HarbingerPriceFeedData = {
  time: Date
  price: Mutez
}

/**
 * Interacts with a Harbinger Oracle.
 */
export default class HarbingerClient {
  /** A TezosToolkit */
  private readonly tezos: TezosToolkit

  /**
   * Construct a new Oracle Client.
   *
   * @param nodeUrl The URL of the node to connect to.
   * @param normalizerAddress The address of the Normalizer contract to read from.
   */
  public constructor(nodeUrl: string, public readonly normalizerAddress: Address) {
    this.tezos = new TezosToolkit(nodeUrl)
  }

  /**
   * Retrieve price feed data.
   */
  public async getPriceData(): Promise<HarbingerPriceFeedData> {
    const normalizerContract = await this.tezos.contract.at(this.normalizerAddress)
    const normalizerStorage: any = await normalizerContract.storage()
    const assetData = await normalizerStorage.assetMap.get(ASSET_CODE)

    return {
      time: new Date(assetData.lastUpdateTime),
      price: assetData.computedPrice, // Note: assetData.computedPrice is a BigNumber
    }
  }
}
