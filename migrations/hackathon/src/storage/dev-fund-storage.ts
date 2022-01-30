import { substituteVariables } from "@hover-labs/tezos-utils";

type DevFundStorage = {
  administratorAddress: string,
  governorAddress: string,
  tokenAddress: string,
}

export function generateDevFundStorage(config: DevFundStorage) {
  let contractStorage = `
  (Pair 
    (Pair 
      (address %administratorContractAddress) 
      (address %governorContractAddress)
    ) 
    (Pair 
      None
      (Pair 
        0 
        (address %tokenContractAddress)
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %administratorContractAddress)": config.administratorAddress,
    "(address %governorContractAddress)": config.governorAddress,
    "(address %tokenContractAddress)": config.tokenAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}

