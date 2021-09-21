/**
 * Errors that can be received from contracts in the Kolibri system.
 *
 * IMPORTANT: Keep this file in sync with /smart_contracts/helpers/errors.py.
 */
enum ContractErrors {
  // An unknown error occurred. This error code is never propagated from the contracts
  // and only exists in the SDK.
  Unknown = -1,

  // The sender of a contract invocation was required to be a oven.
  NotOven = 1,

  // The sender of a contract invocation was required to be the Oven Proxy contract.
  NotOvenProxy = 2,

  // The sender of a contract invocation was required to be the Oracle contract.
  NotOracle = 3,

  // The sender of a contract invocation was required to be the Governor contract.
  NotGovernor = 4,

  // The sender of the contract invocation was required to be the Minter contract.
  NotMinter = 5,

  // The sender of an operation was required to be the owner of the Oven contract.
  NotOwner = 6,

  // The sender of an operation was required to be the Oven Factory contract.
  NotOvenFactory = 7,

  // The sender of an operation was required to be the Administrator of the contract.
  NotAdmin = 8,

  // The sender of an operation was required to be the Pause Guardian.
  NotPauseGuardian = 9,

  // The operation required the oven to be under collateralized.
  NotUnderCollateralized = 10,

  // The operation caused the oven to become under collateralized.
  OvenUnderCollateralized = 11,

  // The state machine of the contract was not in the expected state.
  BadState = 12,

  // The destination message was routed to the wrong smart contract.
  BadDestination = 13,

  // The result contained data for an unexpected asset.
  WrongAsset = 14,

  // The request was not allowed to send an amount.
  AmountNotAllowed = 15,

  // The operation could not be completed because the oven was liquidated.
  Liquidated = 16,

  // The data provided was too old.
  StaleData = 17,

  // The system is paused.
  Paused = 18,

  // Cannot receive funds.
  CannotReceiveFunds = 19,

  // The debt ceiling would be exceeded if the operation were completed.
  DebtCeiling = 20,

  // The Oven was past the maximum allowed value.
  OvenMaximumExceeded = 21,

  // The user was not allowed to perform a token transfer.
  TokenNoTransferPermission = 22,

  // The user did not have a sufficient token balance to complete the operation.
  TokenInsufficientBalance = 23,

  // The allowance change was unsafe. Please reset the allowance to zero before trying to operation again.
  TokenUnsafeAllowanceChange = 23,

  // The operation was not performed by the token administrator.
  TokenNotAdministrator = 24,

  // The operation was not performed by the savings account.
  NotSavingsAccount = 25,
}

export default ContractErrors
