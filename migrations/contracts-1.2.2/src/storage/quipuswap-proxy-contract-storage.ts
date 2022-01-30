import { substituteVariables, objectToMichelson } from "@hover-labs/tezos-utils";

type QuipuswapProxyStorage = {
  governorContractAddress: string,
  harbingerContractAddress: string,
  liquidityPoolContractAddress: string,
  maxDataDelaySec: number,
  pauseGuardianContractAddress: string,
  quipuswapContractAddress: string,
  slippageTolerance: number
}

export async function generateQuipuswapProxyStorage(config: QuipuswapProxyStorage) {
  let contractStorage = `
  (Pair 
    (Pair 
      (Pair 
        (address %governorContractAddress) 
        (address %harbingerContractAddress)
      ) 
      (Pair 
        (address %liquidityPoolContractAddress) 
        (nat %maxDataDelaySec)
      )
    ) 
    (Pair 
      (Pair 
        (address %pauseGuardianContractAddress) 
        False
      ) 
      (Pair 
        (address %quipuswapContractAddress) 
        (nat %slippageTolerance)
      )
    )
  );
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %governorContractAddress)": config.governorContractAddress,
    "(address %harbingerContractAddress)": config.harbingerContractAddress,
    "(address %liquidityPoolContractAddress)": config.liquidityPoolContractAddress,
    "(nat %maxDataDelaySec)": config.maxDataDelaySec,
    "(address %pauseGuardianContractAddress) ": config.pauseGuardianContractAddress,
    "(address %quipuswapContractAddress) ": config.quipuswapContractAddress,
    "(nat %slippageTolerance)": config.slippageTolerance,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}


