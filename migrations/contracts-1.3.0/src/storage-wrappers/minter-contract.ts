import { TezosToolkit } from "@taquito/taquito";
import { substituteVariables } from "./wrapper-utils";

export async function generateMinterStorage(
  oldMinterContractAddress: string,
  liquidityPoolContractAddress: string,
  governorContractAddress: string,
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
  const devFundSplit = oldMinterStorage.devFundSplit
  const stabilityFee = oldMinterStorage.stabilityFee
  const stabilityFundContractAddress = oldMinterStorage.stabilityFundContractAddress
  const tokenContractAddress = oldMinterStorage.tokenContractAddress
  const privateOwnerLiquidationThreshold = oldMinterStorage.privateOwnerLiquidationThreshold

  // Formulate a new storage
  let contractStorage = `
  (Pair 
    (Pair 
      (Pair 
        (nat %collateralizationPercentage) 
        (Pair 
          (nat %devFundSplit) 
          (address %developerFundContractAddress)
        )
      ) 
      (Pair 
        (address %governorContractAddress) 
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
          (address %liquidityPoolContractAddress) 
          (address %ovenProxyContractAddress)
        )
      ) 
      (Pair 
        (Pair 
          (nat %privateOwnerLiquidationThreshold) 
          (nat %stabilityFee)
        ) 
        (Pair 
          (address %stabilityFundContractAddress) 
          (address %tokenContractAddress)
        )
      )
    )
  )
`


  contractStorage = substituteVariables(contractStorage, {
    "(nat %collateralizationPercentage)": collateralizationPercentage,
    "(nat %devFundSplit)": devFundSplit,
    "(address %developerFundContractAddress)": developerFundContractAddress,
    "(address %governorContractAddress)": governorContractAddress,
    "(nat %interestIndex)": interestIndex,
    "(timestamp %lastInterestIndexUpdateTime)": lastInterestIndexUpdateTime,
    "(nat %liquidationFeePercent)": liquidationFeePercent,
    "(address %liquidityPoolContractAddress)": liquidityPoolContractAddress,
    "(address %ovenProxyContractAddress)": ovenProxyContractAddress,
    "(nat %privateOwnerLiquidationThreshold)": privateOwnerLiquidationThreshold,
    "(nat %stabilityFee)": stabilityFee,
    "(address %stabilityFundContractAddress)": stabilityFundContractAddress,
    "(address %tokenContractAddress)": tokenContractAddress,
  })


  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}