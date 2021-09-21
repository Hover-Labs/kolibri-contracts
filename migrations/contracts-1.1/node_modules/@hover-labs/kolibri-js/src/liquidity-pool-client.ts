import Address from './types/address'
import { TezosToolkit, TransactionWalletOperation } from '@taquito/taquito'
import { ThanosWallet } from '@thanos-wallet/dapp'
import { InMemorySigner } from '@taquito/signer'
import { TransactionOperation } from '@taquito/taquito/dist/types/operations/transaction-operation'

/**
 * Controls interaction with the Kolibri Liquidity Pool.
 */
export default class LiquidityPoolClient {
  /** A TezosToolkit */
  private readonly tezos: TezosToolkit

  /**
   * Create a new Liquidity Pool Client.
   *
   * @param nodeUrl The URL of the node to connect to.
   * @param wallet The wallet which will interact with this Oven.
   * @param liquidityPoolAddress The address of the Kolibri Liquidity Pool.
   */
  public constructor(
    nodeUrl: string,
    wallet: InMemorySigner | ThanosWallet,
    public readonly liquidityPoolAddress: Address,
  ) {
    const tezos = new TezosToolkit(nodeUrl)

    // TODO(keefertaylor): Refactor this to be less nonsense.
    if (wallet instanceof InMemorySigner) {
      // Wallet is InMemorySigner
      tezos.setProvider({ signer: wallet })
    } else {
      // Wallet is Thanos Wallet
      tezos.setWalletProvider(wallet)
    }

    this.tezos = tezos
  }

  /**
   * Liquidate an Oven using the liquidity pool.
   *
   * @param targetOvenAddress The oven to liquidate.
   * @returns The operation hash
   */
  public async liquidate(targetOvenAddress: Address): Promise<TransactionOperation | TransactionWalletOperation> {
    const liquidityPoolContract = await this.tezos.wallet.at(this.liquidityPoolAddress)
    const sendArgs = { amount: 0, mutez: true }
    return await liquidityPoolContract.methods['liquidate'](targetOvenAddress).send(sendArgs)
  }
}
