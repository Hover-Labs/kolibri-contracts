import { substituteVariables } from "@hover-labs/tezos-utils";
import { TezosToolkit } from '@taquito/taquito'

type StabilityFundStorage = {
  governorContractAddress: string
  savingsAccountContractAddress: string
}

export async function generateStabilityFundStorage(config: StabilityFundStorage, oldStabilityFundAddress: string, tezos: TezosToolkit) {
  // Grab old values from storage
  const oldStabilityFundContract = await tezos.contract.at(oldStabilityFundAddress)
  const oldStabilityFundStorage: any = await oldStabilityFundContract.storage()

  const fundAdministratorContractAddress = oldStabilityFundStorage.administratorContractAddress
  const ovenRegistryContractAddress = oldStabilityFundStorage.ovenRegistryContractAddress
  const tokenContractAddress = oldStabilityFundStorage.tokenContractAddress

  let contractStorage = `
  (Pair 
    (Pair 
      (address %administratorContractAddress) 
      (Pair 
        (address %governorContractAddress) 
        (address %ovenRegistryContractAddress)
      )
    ) 
    (Pair 
      (Pair 
        (address %savingsAccountContractAddress) 
        None
      ) 
      (Pair 
        0
        (address %tokenContractAddress)
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %administratorContractAddress)": fundAdministratorContractAddress,
    "(address %governorContractAddress)": config.governorContractAddress,
    "(address %ovenRegistryContractAddress)": ovenRegistryContractAddress,
    "(address %savingsAccountContractAddress)": config.savingsAccountContractAddress,
    "(address %tokenContractAddress)": tokenContractAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}


