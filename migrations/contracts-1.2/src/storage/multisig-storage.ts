import { substituteVariables } from "@hover-labs/tezos-utils";

export const generateMultisigStorage = (publicKeys: Array<string>, threshold: number, timelockSeconds: number) => {
  // Sort public keys alphabetically (required by Tezos) and make into a Michelson list.
  // This is a workaround since `substituteVars` can't generate lists (yet)!
  const sortedPublicKeys = publicKeys.sort()
  const michelsonPublicKeyList = sortedPublicKeys.reduce(
    (previous: string, current: string) => {
      return `${previous} "${current}"`
    },
    '',
  )

  let contractStorage = `
  (Pair 
    (Pair 
      (nat %operationId) 
      {${michelsonPublicKeyList}}
    ) 
    (Pair 
      (nat %threshold) 
      (Pair 
        (big_map %timelock nat (Pair timestamp (lambda unit (list operation)))) 
        (nat %timelockSeconds)
      )
    )
  )
  `

  contractStorage = substituteVariables(contractStorage, {
    "(nat %operationId)": 0,
    "(nat %threshold)": threshold,
    "(big_map %timelock nat (Pair timestamp (lambda unit (list operation))))": {},
    "(nat %timelockSeconds)": timelockSeconds
  })

  if (contractStorage.includes("%")) {
    throw new Error("It appears we didn't substitute all variables in the contractStorage! Please check that you're substituting the entire set of variables for the initial storage.")
  }

  return contractStorage
}
