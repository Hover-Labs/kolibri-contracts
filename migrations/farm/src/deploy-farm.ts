import BigNumber from "bignumber.js";
import { substituteVariables, sendOperation, ContractOriginationResult, deployContract, NetworkConfig, checkConfirmed } from "@hover-labs/tezos-utils";
import { KeyStore, TezosNodeReader } from 'conseiljs'
import { NETWORK_CONFIG } from "config.mainnet";
import { TezosToolkit } from "@taquito/taquito";
import { KOLIBRI_CONFIG } from "config";

/** This file shamelessly adapted from https://github.com/Hover-Labs/governance-deploy-scripts */

type FarmStorage = {
  admin: string,
  inputToken: string,
  rewardReserve: string,
  rewardToken: string,
  delegators: object,
  accumulatedRewardPerShare: number
  paid: number,
  unpaid: number
  lastBlockUpdate: number,
  rewardPerBlock: number,
  totalBlocks: number
  farmLpTokenBalance: number
}

export function generateFarmStorage(config: FarmStorage) {
  let contractStorage = `
  (Pair
    (Pair
      (Pair 
        (Pair 
          (address %admin) 
          (address %lpTokenContract)
        )
        (Pair 
          (address %rewardReserve)
          (address %rewardTokenContract)
        )
      )
      (big_map %delegators address (Pair (nat %accumulatedRewardPerShareStart) (nat %lpTokenBalance)))
    )
    (Pair
      (Pair
        (Pair 
          (nat %accumulatedRewardPerShare)
          (Pair 
            (nat %paid) 
            (nat %unpaid)
          )
        )
        (Pair 
          (nat %lastBlockUpdate)
          (Pair 
            (nat %rewardPerBlock) 
            (nat %totalBlocks)
          )
        )
      )
      (nat %farmLpTokenBalance)
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %admin)": config.admin,
    "(address %lpTokenContract)": config.inputToken,
    "(address %rewardReserve)": config.rewardReserve,
    "(address %rewardTokenContract)": config.rewardToken,
    "(big_map %delegators address (Pair (nat %accumulatedRewardPerShareStart) (nat %lpTokenBalance)))": config.delegators,
    "(nat %accumulatedRewardPerShare)": config.accumulatedRewardPerShare,
    "(nat %paid)": config.paid,
    "(nat %unpaid)": config.unpaid,
    "(nat %lastBlockUpdate)": config.lastBlockUpdate,
    "(nat %rewardPerBlock)": config.rewardPerBlock,
    "(nat %totalBlocks)": config.totalBlocks,
    "(nat %farmLpTokenBalance)": config.farmLpTokenBalance,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}


type FarmReserveStorage = {
  farmAddress: string,
  governorAddress: string,
  initialized: boolean,
  revokeAddress: string,
  rewardTokenAddress: string
}

export function generateFarmReserveStorage(config: FarmReserveStorage) {
  let contractStorage = `
  (Pair 
    (Pair 
      (address %farmAddress) 
      (address %governorAddress)
    )
    (Pair 
      (bool %initialized)
      (Pair 
        (address %revokeAddress) 
        (address %rewardTokenAddress)
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %farmAddress)": config.farmAddress,
    "(address %governorAddress)": config.governorAddress,
    "(bool %initialized)": config.initialized,
    "(address %revokeAddress)": config.revokeAddress,
    "(address %rewardTokenAddress)": config.rewardTokenAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}

export async function deployReserve(
  communityFundAdddress: string,
  rewardToken: string,
  contractSources: any,
  networkConfig: NetworkConfig,
  tezos: TezosToolkit,
): Promise<ContractOriginationResult> {
  const deployer = await tezos.signer.publicKeyHash()

  const reserveStorage = generateFarmReserveStorage(
    {
      farmAddress: deployer, // To be updated
      governorAddress: deployer, // To be updated
      initialized: false,
      revokeAddress: communityFundAdddress,
      rewardTokenAddress: rewardToken
    }
  )

  const reserveDeployResult = await deployContract(
    networkConfig,
    tezos,
    contractSources.reserveContract,
    reserveStorage
  )
  console.log('Deployed.')
  console.log('')

  return reserveDeployResult
}

export async function deployFarm(
  contractSources: any,
  depositToken: string,
  reserveAddress: string,
  rewardToken: string,
  networkConfig: NetworkConfig,
  tezos: TezosToolkit
): Promise<ContractOriginationResult> {
  const deployer = await tezos.signer.publicKeyHash()
  const farmStorage = generateFarmStorage(
    {
      admin: deployer, // To be updated later
      inputToken: depositToken,
      rewardReserve: reserveAddress,
      rewardToken: rewardToken,
      delegators: {},
      accumulatedRewardPerShare: 0,
      paid: 0,
      unpaid: 0,
      lastBlockUpdate: 0,
      rewardPerBlock: 0, // To be updated later
      totalBlocks: 0, // To be updated later
      farmLpTokenBalance: 0 // To be updated later.
    }
  )

  const farmDeployResult = await deployContract_legacy(
    networkConfig,
    tezos,
    contractSources.farmContract,
    farmStorage,
  )
  console.log('Deployed.')
  console.log('')

  return farmDeployResult
}

export type FarmingSystemConfig = {
  inputTokenAddress: string,
  totalRewards: BigNumber,
  rewardPerBlock: BigNumber,
  totalBlocks: BigNumber
}

export type FarmingSystemDeployResult = {
  farmDeployResult: ContractOriginationResult
  reserveDeployResult: ContractOriginationResult
}

export async function deployAndWireFarmingSystem(
  contractSources: any,
  farmingSystemConfig: FarmingSystemConfig,
  daoAddress: string,
  communityFundAdddress: string,
  kdaoAddress: string,
  networkConfig: NetworkConfig,
  tezos: TezosToolkit
): Promise<FarmingSystemDeployResult> {
  const farmingSystemDeployResult = await deployFarmingSystem(
    contractSources,
    farmingSystemConfig,
    communityFundAdddress,
    kdaoAddress, networkConfig, tezos
  )

  await wireFarmingSystem(
    farmingSystemDeployResult,
    farmingSystemConfig,
    daoAddress, networkConfig, tezos
  )

  return farmingSystemDeployResult
}

async function deployFarmingSystem(
  contractSources: any,
  farmingSystemConfig: FarmingSystemConfig,
  communityFundAdddress: string,
  kdaoAddress: string,
  networkConfig: NetworkConfig,
  tezos: TezosToolkit,
): Promise<FarmingSystemDeployResult> {
  console.log('>>> [1/2] Deploying Reserve Contract...')
  const reserveDeployResult = await deployReserve(
    communityFundAdddress,
    kdaoAddress,
    contractSources, networkConfig, tezos
  )

  console.log('>>> [2/2] Deploying Farm Contract...')
  const farmDeployResult = await deployFarm(
    contractSources,
    farmingSystemConfig.inputTokenAddress,
    reserveDeployResult.contractAddress,
    kdaoAddress,  networkConfig, tezos
  )

  return {
    farmDeployResult,
    reserveDeployResult
  }
}

async function wireFarmingSystem(
  farmingSystemDeployResult: FarmingSystemDeployResult,
  farmingSystemConfig: FarmingSystemConfig,
  // kdaoAddress: string,
  daoAddress: string,
  networkConfig: NetworkConfig, 
  tezos: TezosToolkit,
) {
  console.log('>>> [1/5] Initializing Farm Reward Reserve')
  await sendOperation(
    networkConfig, tezos, farmingSystemDeployResult.reserveDeployResult.contractAddress, 'initialize', farmingSystemDeployResult.farmDeployResult.contractAddress,
  )
  console.log('')

  console.log('>>> [2/5] Asking reserve to give farm an allowance')
  await sendOperation(
    networkConfig, tezos,
    farmingSystemDeployResult.reserveDeployResult.contractAddress,
    'giveRewardAllowance',
    farmingSystemConfig.totalRewards,
  )
  console.log('')

  // console.log('>>> [3/5] Setting reward plan on farm')
  // await sendOperation(
  //   networkConfig, tezos,
  //   farmingSystemDeployResult.farmDeployResult.contractAddress,
  //   'updatePlan',
  //   [ farmingSystemConfig.rewardPerBlock, farmingSystemConfig.totalBlocks ]
  // )
  // console.log('')

  console.log('>>> [4/5] Setting Governor on Reserve')
  await sendOperation(
    networkConfig, tezos,
    farmingSystemDeployResult.reserveDeployResult.contractAddress,
    'setGovernorContract',
    daoAddress,
  )
  console.log('')

  console.log('>>> [5/5] Setting Governor on Farm')
  await sendOperation(
    networkConfig, tezos,
    farmingSystemDeployResult.farmDeployResult.contractAddress,
    'setAdmin',
    daoAddress,
  )
  console.log('')
}

/** Farms are in JSON and tezos-utils can't handle that, so use this legacy method. */
export async function deployContract_legacy(
  networkConfig: NetworkConfig, tezos: TezosToolkit, contractSource: string,
  storage: string,
): Promise<ContractOriginationResult> {

  console.log("Contract source: "+ contractSource)


  try {
    console.log(`Using storage: ${storage}`)

    const result = await tezos.contract.originate({
      code: JSON.parse(contractSource),
      init: storage,
    })

    console.log(`Deployed in hash: ${result.hash}`)
    console.log(`Deployed contract: ${result.contractAddress}`)
    console.log('')

    console.log("Awaiting confirmation...")
    await checkConfirmed(networkConfig, result.hash)
    console.log("Confirmed!")

    return {
      operationHash: result.hash,
      contractAddress: result.contractAddress || "ERR",
    }
  } catch (e) {
    console.log('Caught exception, retrying...')
    console.error(e)

    return deployContract_legacy(
      networkConfig, tezos, contractSource,
      storage,
    )
  }
}