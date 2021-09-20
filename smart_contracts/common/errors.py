################################################################
# Errors from Kolibri contracts.
#
#  IMPORTANT: Keep this file in sync with /sdk/src/contract-errors.py.
################################################################

# The sender of a contract invocation was required to be a oven.
NOT_OVEN = 1

# The sender of a contract invocation was required to be the Oven Proxy contract.
NOT_OVEN_PROXY = 2

# The sender of a contract invocation was required to be the Oracle contract.
NOT_ORACLE = 3

# The sender of a contract invocation was required to be the Governor contract.
NOT_GOVERNOR = 4

# The sender of the contract invocation was required to be the Minter contract.
NOT_MINTER = 5

# The sender of an operation was required to be the owner of the Oven contract.
NOT_OWNER = 6

# The sender of an operation was required to be the Oven Factory contract.
NOT_OVEN_FACTORY = 7

# The sender of an operation was required to be the Administrator of the contract.
NOT_ADMIN = 8

# The sender of an operation was required to be the Pause Guardian.
NOT_PAUSE_GUARDIAN = 9

# The operation required the oven to be under collateralized.
NOT_UNDER_COLLATERALIZED = 10

# The operation caused the oven to become under collateralized.
OVEN_UNDER_COLLATERALIZED = 11

# The state machine of the contract was not in the expected state.
BAD_STATE = 12

# The destination message was routed to the wrong smart contract.
BAD_DESTINATION = 13

# The result contained data for an unexpected asset.
WRONG_ASSET = 14

# The request was not allowed to send an amount.
AMOUNT_NOT_ALLOWED = 15

# The operation could not be completed because the oven was liquidated.
LIQUIDATED = 16

# The data provided was too old.
STALE_DATA = 17

# The system is paused.
PAUSED = 18

# Cannot receive funds.
CANNOT_RECEIVE_FUNDS = 19

# The debt ceiling would be exceeded if the operation were completed. 
DEBT_CEILING = 20

# The Oven was past the maximum allowed value.
OVEN_MAXIMUM_EXCEEDED = 21

# The user was not allowed to perform a token transfer.
TOKEN_NO_TRANSFER_PERMISSION = 22

# The user did not have a sufficient token balance to complete the operation.
TOKEN_INSUFFICIENT_BALANCE = 23

# The allowance change was unsafe. Please reset the allowance to zero before trying to operation again.
TOKEN_UNSAFE_ALLOWANCE_CHANGE = 23

# The operation was not performed by the token administrator.
TOKEN_NOT_ADMINISTRATOR = 24