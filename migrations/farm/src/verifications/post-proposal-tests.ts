import { approveToken, checkConfirmed, ContractOriginationResult, fetchFromCache, getTezos, validateBreakGlass, validateStorageValue, sleep, getSigner, getTokenBalanceFromDefaultSmartPyContract, CONSTANTS } from "@hover-labs/tezos-utils"
import CACHE_KEYS from "../cache-keys"
import { MIGRATION_CONFIG, NETWORK_CONFIG } from "../config"
import BigNumber from 'bignumber.js'
import { OvenClient, StableCoinClient, Network, HarbingerClient, deriveOvenAddress, SavingsPoolClient } from "@hover-labs/kolibri-js"
import _ from "lodash";
import { TransactionWalletOperation, TezosToolkit } from '@taquito/taquito'
import { KOLIBRI_CONFIG } from "../config"

async function verifyFarm(
  farmAddress: string,
  rewardReserveAddress: string,
  inputTokenAddress: string,
  daoAddress: string,
  kDAOAddress: string,
  totalFarmBalance: BigNumber,
  rewardPerBlock: BigNumber,
  tezos: TezosToolkit
): Promise<void> {
  const farmContract = await tezos.contract.at(farmAddress)
  const farmStorage: any = await farmContract.storage()

  // Admin should be the DAO
  if (farmStorage.addresses.admin != daoAddress) {
      throw new Error("Bad farm admin!")
  }

  // LP token should be the input token
  if (farmStorage.addresses.lpTokenContract != inputTokenAddress) {
      throw new Error("Bad input token!")
  }

  // Reward reserve should be the reward reserve.
  if (farmStorage.addresses.rewardReserve != rewardReserveAddress) {
      throw new Error("Bad reward reserve!")
  }

  // Reward token contract should be kDAO
  if (farmStorage.addresses.rewardTokenContract != kDAOAddress) {
      throw new Error("Bad reward token!")
  }

  // Farm should have an allowance from the reserve
  const tokenContract = await tezos.contract.at(kDAOAddress)
  const tokenStorage: any = await tokenContract.storage()
  const approvals = await tokenStorage.approvals.get(rewardReserveAddress)
  const allowance =
      (approvals === undefined) ? new BigNumber(0) : new BigNumber(approvals.get(farmAddress))
  if (!allowance.isEqualTo(totalFarmBalance)) {
      throw new Error("Bad allowance!")
  }

  // Farm should be giving out the correct balance per block
  const perBlock = farmStorage.farm.plannedRewards.rewardPerBlock
  if (!perBlock.isEqualTo(rewardPerBlock)) {
      throw new Error("Bad reward rate!")
  }
}


const main = async () => {
  console.log("Validating farm")
  console.log("")

  const farmData: any = await fetchFromCache(CACHE_KEYS.FARMING_SYSTEM)
  const farmAddress = farmData.farmDeployResult.contractAddress
  const reserveAddress = farmData.reserveDeployResult.contractAddress

  const daoAddress = KOLIBRI_CONFIG.contracts.DAO!
  const daoTokenAddress = KOLIBRI_CONFIG.contracts.DAO_TOKEN!
  
  const tezos = await getTezos(NETWORK_CONFIG)

  console.log("Validating farm...")
  await verifyFarm(
    farmAddress,
    reserveAddress,
    MIGRATION_CONFIG.farmingConfig.inputTokenAddress,
    daoAddress,
    daoTokenAddress,
    MIGRATION_CONFIG.farmingConfig.totalRewards,
    MIGRATION_CONFIG.farmingConfig.rewardPerBlock,
    tezos,
  )
  console.log("   / passed")

  console.log("")
  console.log("All Tests Pass!")
}
main()