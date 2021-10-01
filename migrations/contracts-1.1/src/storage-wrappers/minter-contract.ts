import { TezosToolkit } from "@taquito/taquito";
import { substituteVariables } from "./wrapper-utils";

type MinterStorage = {
  collateralizationPercentage: number
  developerFundContractAddress: string
  governorContractAddress: string
  interestIndex: number
  lastInterestIndexUpdateTime: any
  liquidationFeePercent: number
  ovenProxyContractAddress: string
  devFundSplit: number
  stabilityFee: number
  stabilityFundContractAddress: string
  tokenContractAddress: string,
  liquidityPoolContractAddress: string,
  privateOwnerLiquidationThreshold: number
}

export async function generateMinterStorage(
  oldMinterContractAddress: string,
  liquidityPoolContractAddress: string,
  governorContractAddress: string,
  privateOwnerLiquidationThreshold: number,
  config: any
) {
  // Grab old values from storage
  const tezos: TezosToolkit = await config.getTezos()
  const oldMinterContract = await tezos.contract.at(oldMinterContractAddress)
  const oldMinterStorage: any = await oldMinterContract.storage()

  const collateralizationPercentage = oldMinterStorage.collateralizationPercentage
  const developerFundContractAddress = oldMinterStorage.developerFundContractAddress
  const interestIndex = oldMinterStorage.interestIndex
  const lastInterestIndexUpdateTime = new Date(oldMinterStorage.lastInterestIndexUpdateTime).getTime() / 1000
  const liquidationFeePercent = oldMinterStorage.liquidationFeePercent
  const ovenProxyContractAddress = oldMinterStorage.ovenProxyContractAddress
  const devFundSplit = oldMinterStorage.stabilityDevFundSplit
  const stabilityFee = oldMinterStorage.stabilityFee
  const stabilityFundContractAddress = oldMinterStorage.stabilityFundContractAddress
  const tokenContractAddress = oldMinterStorage.tokenContractAddress

  // Formulate a new storage
  let contractStorage = `
  (Pair 
    (Pair 
      (Pair 
        (nat %collateralizationPercentage) 
        (Pair 
          (nat %devFundSplit) 
          (address %devFundAddress)
        )
      ) 
      (Pair 
        (address %governorAddress)
        (Pair 
          (nat %interestIndex) 
          (timestamp %lastInterestIndexUpdateTime)
        )
      )
    ) 
    (Pair 
      (Pair
        (nat %liquidationFeePercent) 
        (Pair 
          (address %liquidityPoolAddress) 
          (address %ovenProxyAddress)
        )
      ) 
      (Pair 
        (Pair 
          (nat %privateOwnerLiquidationThreshold) 
          (nat %stabilityFee)
        ) 
        (Pair 
          (address %stabilityFundAddress) 
          (address %tokenAddress)
        )
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(nat %collateralizationPercentage)": collateralizationPercentage,
    "(nat %devFundSplit)": devFundSplit,
    "(address %devFundAddress)": developerFundContractAddress,
    "(address %governorAddress)": governorContractAddress,
    "(nat %interestIndex)": interestIndex,
    "(timestamp %lastInterestIndexUpdateTime)": lastInterestIndexUpdateTime,
    "(nat %liquidationFeePercent)": liquidationFeePercent,
    "(address $liquidityPoolAddress)": liquidityPoolContractAddress,
    "(address %ovenProxyAddress)": ovenProxyContractAddress,
    "(nat %privateOwnerLiquidationThreshold)": privateOwnerLiquidationThreshold,
    "(nat %stabilityFee)": stabilityFee,
    "(address %stabilityFundAddress)": stabilityFundContractAddress,
    "(address %tokenAddress)": tokenContractAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}