import Address from './types/address'
import { TezosToolkit, TransactionWalletOperation } from '@taquito/taquito'
import { ThanosWallet } from '@thanos-wallet/dapp'
import { InMemorySigner } from '@taquito/signer'
import HarbingerClient from './harbinger-client'
import Mutez from './types/mutez'
import Shard from './types/shard'
import { TransactionOperation } from '@taquito/taquito/dist/types/operations/transaction-operation'
import StableCoinClient from './stable-coin-client'

import BigNumber from 'bignumber.js'

// Conversion constant to change mutez into shard precision.
// TODO(keefertaylor): Refactor into a utils class.
const MUTEZ_DIGITS = 6
const SHARD_DIGITS = 18

const MUTEZ_TO_SHARD = new BigNumber(Math.pow(10, SHARD_DIGITS - MUTEZ_DIGITS))
const SHARD_PRECISION = new BigNumber(Math.pow(10, SHARD_DIGITS))

/**
 * Controls interaction with an Oven.
 */
export default class OvenClient {
  /** A TezosToolkit */
  private readonly tezos: TezosToolkit

  /**
   * Create a new OvenClient.
   *
   * @param nodeUrl The URL of the node to connect to.
   * @param wallet The wallet which will interact with this Oven.
   * @param ovenAddress The address of the oven.
   * @param stableCoinClient The stable coin client
   * @param harbingerClient The harbinger price oracle client
   */
  public constructor(
    nodeUrl: string,
    wallet: InMemorySigner | ThanosWallet,
    public readonly ovenAddress: Address,
    public readonly stableCoinClient: StableCoinClient,
    public readonly harbingerClient: HarbingerClient,
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
   * Retrieve the collateralization ratio of the oven.
   *
   * @returns The collateralization ratio as a shard.
   */
  public async getCollateralizationRatio(): Promise<Shard> {
    // Get price as a shard.
    const { price } = await this.harbingerClient.getPriceData()
    const priceShard = price.multipliedBy(MUTEZ_TO_SHARD)
    const currentBalance = await this.getBalance()
    // Get value of collateral as a shard.
    const collateralValue = currentBalance.multipliedBy(MUTEZ_TO_SHARD).multipliedBy(priceShard)
    const collateralValueInkUSD = collateralValue.multipliedBy(SHARD_PRECISION)

    // Get borrowed collateral as a shard.
    const totalBorrowedTokens = await this.getTotalOutstandingTokens()

    // TODO(keefertaylor): Refactor this to utils for re-use.
    return collateralValueInkUSD.dividedBy(totalBorrowedTokens).multipliedBy(new BigNumber(100))
  }

  /**
   * Retrieve the baker for the oven.
   *
   * @returns The baker for the oven.
   */
  public async getBaker(): Promise<Address | null> {
    try {
      return await this.tezos.rpc.getDelegate(this.ovenAddress)
    } catch (e: any) {
      // If 404 was received then the baker is actually just null.
      // See:
      // - https://github.com/ecadlabs/taquito/issues/556
      // - https://gitlab.com/tezos/tezos/-/issues/490
      if (e.status === 404) {
        return null
      }

      // If another error occurred, rethrow.
      throw e
    }
  }

  /**
   * Set the baker of the oven.
   *
   * @param baker The baker for the oven.
   * @returns The operation hash
   */
  public async setBaker(baker: Address | null): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('setDelegate', baker)
  }

  /**
   * Retrieve the owner of the oven.
   *
   * @returns The address which owns the oven.
   */
  public async getOwner(): Promise<Address> {
    const ovenContract = await this.tezos.wallet.at(this.ovenAddress)
    const ovenStorage: any = await ovenContract.storage()
    return ovenStorage.owner
  }

  /**
   * Retrieve the number of tokens borrowed against the oven.
   *
   * NOTE: This method does *NOT* include stability fees. Please see:
   * `getStabilityFees` and `getTotalOutstandingTokens`.
   *
   * @returns The amount of tokens borrowed.
   */
  public async getBorrowedTokens(): Promise<Shard> {
    const ovenContract = await this.tezos.wallet.at(this.ovenAddress)
    const ovenStorage: any = await ovenContract.storage()
    return ovenStorage.borrowedTokens
  }

  /**
   * Retrieve the total number of tokens outstanding on the vault.
   *
   * This method includes the stability fees and borrowed tokens. For individual
   * breakdowns, see `getStabilityFees` and `getBorrowedTokens`.
   *
   * @param time The time to calculate the values at. Defaults to the current time.
   * @returns The amount of tokens owed in stability fees.
   */
  public async getTotalOutstandingTokens(time: Date = new Date()): Promise<Shard> {
    const stabilityFees = await this.getStabilityFees(time)
    const borrowedTokens = await this.getBorrowedTokens()
    return stabilityFees.plus(borrowedTokens)
  }

  /**
   * Retrieve the number of tokens owed in stability fees against the oven.
   *
   * @param time The time to calculate the values at. Defaults to the current time.
   * @returns Interest rate data for the system.
   */
  public async getStabilityFees(time: Date = new Date()): Promise<Shard> {
    const ovenContract = await this.tezos.wallet.at(this.ovenAddress)
    const ovenStorage: any = await ovenContract.storage()
    const stabilityFeeTokens: BigNumber = ovenStorage.stabilityFeeTokens

    const interestData = await this.stableCoinClient.getInterestData(time)
    const ovenInterestIndex: BigNumber = ovenStorage.interestIndex
    const borrowedTokens = await this.getBorrowedTokens()
    const minterInterestIndex: BigNumber = interestData.globalInterestIndex

    const ratio = minterInterestIndex.times(SHARD_PRECISION).div(ovenInterestIndex).integerValue()
    const totalPrinciple = borrowedTokens.plus(stabilityFeeTokens)
    const newTotalTokens = ratio.times(totalPrinciple).div(SHARD_PRECISION).integerValue()
    return newTotalTokens.minus(borrowedTokens)
  }

  /**
   * Query if the Oven is liquidated.
   *
   * @returns A boolean representing the liquidation state.
   */
  public async isLiquidated(): Promise<boolean> {
    const ovenContract = await this.tezos.wallet.at(this.ovenAddress)
    const ovenStorage: any = await ovenContract.storage()
    return ovenStorage.isLiquidated
  }

  /**
   * Get the balance of the oven.
   *
   * @returns The oven balance in mutez.
   */
  public async getBalance(): Promise<Mutez> {
    return await this.tezos.tz.getBalance(this.ovenAddress)
  }

  /**
   * Liquidate an Oven.
   *
   * @returns The operation hash.
   */
  public async liquidate(): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('liquidate', [['unit']])
  }

  /**
   * Borrow tokens against an Oven's collateral.
   *
   * @param tokens The number of tokens to borrow.
   * @returns The operation hash.
   */
  public async borrow(tokens: Shard): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('borrow', tokens)
  }

  /**
   * Deposit XTZ into the Oven.
   *
   * @param mutez The amount of XTZ to deposit, specified in mutez.
   * @returns The operation hash.
   */
  public async deposit(mutez: Mutez): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('default', [['unit']], Number(mutez))
  }

  /**
   * Withdraw XTZ from the Oven.
   *
   * @param mutez The amount of XTZ to withdraw, specified in mutez.
   * @returns The operation hash.
   */
  public async withdraw(mutez: Mutez): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('withdraw', mutez)
  }

  /**
   * Repay borrowed tokens.
   *
   * @param tokensToRepay The number of tokens to repay.
   * @returns The operation hash.
   */
  public async repay(tokensToRepay: Shard): Promise<TransactionOperation | TransactionWalletOperation> {
    return this.invokeOvenMethod('repay', tokensToRepay)
  }

  /**
   * Invoke a method in the oven contract.
   *
   * @param entrypoint The entry point to invoke.
   * @param args The arguments to send with the invocation.
   * @param amount The amount of XTZ to send with the operation, specified in mutez.
   * @returns The operation hash.
   */
  private async invokeOvenMethod(
    entrypoint: string,
    args: any,
    amount = 0,
  ): Promise<TransactionOperation | TransactionWalletOperation> {
    const ovenContract = await this.tezos.wallet.at(this.ovenAddress)
    const sendArgs = { amount: amount, mutez: true }
    return await ovenContract.methods[entrypoint](args).send(sendArgs)
  }
}
