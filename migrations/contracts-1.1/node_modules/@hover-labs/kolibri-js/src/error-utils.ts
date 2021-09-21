/* Allow typing as `any`. */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */

import ContractError from './contract-errors'

/** A identifier for an item that will hold an explicit reason for the script failing. */
const ERROR_ID_SCRIPT_REJECTED = 'proto.007-PsDELPH1.michelson_v1.script_rejected'

const ErrorUtils = {
  /**
   * Attempt to parse a ContractError from an exception thrown from Taquito.
   *
   * If the exception is not in the expected form, or an error cannot be found
   * then this function will return ContractError.Unknown.
   *
   * @param exception The exception to parse.
   * @returns The associated error code if parseable, otherwise ContractError.Unknown.
   */
  contractErrorFromTaquitoException: function (exception: any): ContractError {
    // Retrieve the errors array and bail if it doesn't exist.
    const errors: Array<any> = exception.errors
    if (errors === undefined) {
      return ContractError.Unknown
    }

    // Loop through each item in the errors array, searching for an error that has
    // a code attached.
    for (let i = 0; i < errors.length; i++) {
      const error = errors[i]
      const id: string = error.id
      if (id === undefined) {
        continue
      }

      // Search for error IDs that will contain additional info.
      if (id === ERROR_ID_SCRIPT_REJECTED) {
        // Attempt to parse out an error code.
        const withValue = error.with
        if (withValue === undefined) {
          continue
        }

        const errorCodeString: string = withValue.int
        if (errorCodeString === undefined) {
          continue
        }

        const errorCode = parseInt(errorCodeString)
        if (Number.isNaN(errorCode)) {
          continue
        }

        return errorCode
      }
    }

    // If no match was found, return Uknown.
    return ContractError.Unknown
  },
}

export default ErrorUtils
