interface SubstitutionMap {
    [key: string]: any
}

// Substitute and convert to JSON types (which will quote strings properly, leave integers alone, etc etc)
export function substituteVariables(contractStorage: string, substitutionMap: SubstitutionMap) {
    for (const key in substitutionMap) {
        if (substitutionMap.hasOwnProperty(key)) {
            const value = substitutionMap[key]
            let encodedValue = JSON.stringify(value)

            // If object
            if (typeof value === 'object') {
                if (value._isBigNumber) {
                    encodedValue = value.toFixed()
                } else if (Object.keys(value).length !== 0) {
                    throw new Error("Not done yet :P") // TODO: Fix so it doesn't just initialize nothing
                } else {
                    encodedValue = '{}'
                }
            }

            // If we have a pre-serialized bigmap
            if (typeof value === 'string') {
                if ((value.startsWith('{') && value.endsWith('}')) || (value.startsWith('(') && value.endsWith(')'))) {
                    encodedValue = value
                }
            }

            // If nonetype
            if (encodedValue == '"None"') {
                encodedValue = '(None)'
            }

            // If boolean
            if (encodedValue == 'false' || encodedValue == 'true') {
                encodedValue = encodedValue[0].toUpperCase() + encodedValue.slice(1)
            }
            contractStorage = contractStorage.replace(key, encodedValue)
        }
    }
    return contractStorage
}