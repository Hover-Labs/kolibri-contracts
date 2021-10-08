import { substituteVariables } from "@hover-labs/tezos-utils";

type SavingsPoolStorage = {
  governorAddress: string,
  interestRate: number,
  stabilityFundAddress: string,
  tokenAddress: string
}

export async function generateSavingsPoolStorage(config: SavingsPoolStorage,) {
  let contractStorage = `
  (Pair 
    (Pair 
      (Pair 
        {} 
        (Pair 
          (address %governorAddress) 
          (nat %interestRate)
        )
      ) 
      (Pair 
        (Pair 
          "0" 
          {Elt "" 0x74657a6f732d73746f726167653a64617461; Elt "data" 0x7b20226e616d65223a2022496e7465726573742042656172696e67206b555344222c2020226465736372697074696f6e223a2022496e7465726573742042656172696e67206b555344222c202022617574686f7273223a205b22486f766572204c616273203c68656c6c6f40686f7665722e656e67696e656572696e673e225d2c202022686f6d6570616765223a20202268747470733a2f2f6b6f6c696272692e66696e616e6365222c2022696e7465726661636573223a205b2022545a49502d3030372d323032312d30312d3239225d207d}
        ) 
        (Pair 
          None 
          None
        )
      )
    ) 
    (Pair 
      (Pair 
        (Pair 
          None 
          None
        ) 
        (Pair 
          (address %stabilityFundAddress) 
          0
        )
      ) 
      (Pair 
        (Pair 
          (address %tokenAddress)  
          {Elt 0 (Pair 0 {Elt "decimals" 0x3138; Elt "icon" 0x2068747470733a2f2f6b6f6c696272692d646174612e73332e616d617a6f6e6177732e636f6d2f6c6f676f2e706e67; Elt "name" 0x496e7465726573742042656172696e67206b555344; Elt "symbol" 0x69626b555344})}
        ) 
        (Pair 
          0 
          0
        )
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(address %governorAddress)": config.governorAddress,
    "(nat %interestRate)": config.interestRate,
    "(address %stabilityFundAddress)": config.stabilityFundAddress,
    "(address %tokenAddress)": config.tokenAddress,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}


