import smartpy as sp

################################################################
# Common Entry Point Names for the Oven -> Oven Proxy -> Minter Abstraction
################################################################
BORROW_ENTRY_POINT_NAME = "borrow"
REPAY_ENTRY_POINT_NAME = "repay"
DEPOSIT_ENTRY_POINT_NAME = "deposit"
WITHDRAW_ENTRY_POINT_NAME = "withdraw"
LIQUIDATE_ENTRY_POINT_NAME = "liquidate"

################################################################
# Common Parameter types for the Oven -> Oven Proxy -> Minter Abstraction
################################################################

# Borrow parameter type.
# Elements:
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Nat: The additional number of tokens to borrow.
BORROW_PARAMETER_TYPE        =                   sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))

# Borrow parameter type with oracle data attached
# Elements:
#   - Nat: XTZ-USD value as reported by Oracle.
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Nat: The additional number of tokens to borrow.
BORROW_PARAMETER_TYPE_ORACLE = sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))

# Repay parameter type.
# Elements:
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Nat: The number of tokens to repay.
REPAY_PARAMETER_TYPE = sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))

# Withdraw parameter type.
# Elements:
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Mutez: The amount to withdraw.
WITHDRAW_PARAMETER_TYPE        =                   sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez)))))))

# Withdraw parameter type with oracle data attached.
# Elements:
#   - Nat: XTZ-USD value as reported by Oracle.
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Mutez: The amount to withdraw.
WITHDRAW_PARAMETER_TYPE_ORACLE = sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))))

# Deposit parameter type.
# Elements:
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
DEPOSIT_PARAMETER_TYPE = sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt))))))

# Liquidate parameter type.
# Elements:
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Address: The address performing the liquidation
LIQUIDATE_PARAMETER_TYPE        =                   sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))

# Liquidate parameter type with oracle data attached.
# Elements:
#   - Nat: XTZ-USD value as reported by Oracle.
#   - Address: The address of the oven
#   - Address: The address of the owner
#   - Nat: The balance of the oven
#   - Nat: The number of borrowed tokens
#   - Bool: Whether the oven is liquidated.
#   - Int: The number of tokens accrued in stability fees.
#   - Int: The interest index for the oven.
#   - Address: The address performing the liquidation
LIQUIDATE_PARAMETER_TYPE_ORACLE = sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress))))))))

################################################################
# Common Entry Point Names for the Minter -> Oven Proxy -> Oven Abstraction
################################################################

UPDATE_STATE_ENTRY_POINT_NAME = "updateState"

################################################################
# Common Entry Point Names for the Minter -> Oven Proxy -> Oven Abstraction
################################################################

# Update a Ovens's state.
# Elements:
#   - Address: The oven to update
#   - Nat: The new value for borrowed tokens
#   - Int: The new value for accrued stability fees in tokens.
#   - Int: The interest index for the oven.
#   - Bool: The new value for is liquidated.
UPDATE_STATE_PARAMETER_TYPE = sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool))))
