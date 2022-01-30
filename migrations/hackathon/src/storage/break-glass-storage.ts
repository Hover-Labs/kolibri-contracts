import { substituteVariables } from "@hover-labs/tezos-utils";

type BreakGlassStorage = {
  daoAddress: string,
  multisigAddress: string,
  targetAddress: string,
}

export function generateBreakGlassStorage(config: BreakGlassStorage) {
  let contractStorage = `
  (Pair 
    (address %daoAddress) 
    (Pair 
      (address %multisigAddress) 
      (address %targetAddress)
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %daoAddress)": config.daoAddress,
    "(address %multisigAddress)": config.multisigAddress,
    "(address %targetAddress)": config.targetAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}