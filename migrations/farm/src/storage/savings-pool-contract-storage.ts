import { substituteVariables, objectToMichelson } from "@hover-labs/tezos-utils";

type SavingsPoolStorage = {
  governorAddress: string,
  interestRate: number,
  pauseGuardianAddress: string,
  stabilityFundAddress: string,
  tokenAddress: string
}

export async function generateSavingsPoolStorage(config: SavingsPoolStorage,) {
  let contractStorage = `
  (Pair 
    (Pair 
      (Pair 
        (Pair 
          {} 
          (address %governorAddress)
        ) 
        (Pair 
          (nat %interestRate) 
          "1970-01-01T00:00:00Z"
        )
      ) 
      (Pair 
        (Pair 
          (big_map %metadata string bytes)
          (address %pauseGuardianAdress)
        ) 
        (Pair 
          False 
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
          None 
          (address %stabilityFundAddress)
        )
      ) 
      (Pair 
        (Pair 
          0 
          (address %tokenAddress)
        ) 
        (Pair 
          (big_map %token_metadata nat (Pair nat (map string bytes))) 
          (Pair 
            0 
            0
          )
        )
      )
    )
  )
  `

  const metadata = objectToMichelson({
    "": "tezos-storage:data",
    data: JSON.stringify({
      name: 'Kolibri Savings Pool',
      description: "Savings Pool and Savings Pool LP tokens",
      authors: "Hover Labs <hello@hover.engineering>",
      homepage: "https://kolibri.finance",
      interfaces: ["TZIP-007-2021-01-29"]
    })
  })

  const tokenMetadata = objectToMichelson({
    decimals: "36",
    icon: "https://kolibri-data.s3.amazonaws.com/ksr-logo.png",
    name: "Kolibri Savings",
    symbol: "KSR",
  })
  const tokenMetadataWrapped = `{Elt 0 (Pair 0 ${tokenMetadata})}`

  contractStorage = substituteVariables(contractStorage, {
    "(address %governorAddress)": config.governorAddress,
    "(nat %interestRate)": config.interestRate,
    "(address %pauseGuardianAdress)": config.pauseGuardianAddress,
    "(address %stabilityFundAddress)": config.stabilityFundAddress,
    "(address %tokenAddress)": config.tokenAddress,
    "(big_map %metadata string bytes)": metadata,
    "(big_map %token_metadata nat (Pair nat (map string bytes)))": tokenMetadataWrapped,
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}


