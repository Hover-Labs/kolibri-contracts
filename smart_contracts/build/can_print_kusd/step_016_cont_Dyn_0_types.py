import smartpy as sp

tstorage = sp.TRecord(borrowedTokens = sp.TNat, interestIndex = sp.TInt, isLiquidated = sp.TBool, ovenProxyContractAddress = sp.TAddress, owner = sp.TAddress, stabilityFeeTokens = sp.TInt).layout((("borrowedTokens", ("interestIndex", "isLiquidated")), ("ovenProxyContractAddress", ("owner", "stabilityFeeTokens"))))
tparameter = sp.TVariant(borrow = sp.TNat, default = sp.TUnit, liquidate = sp.TUnit, repay = sp.TNat, setDelegate = sp.TOption(sp.TKeyHash), updateState = sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), withdraw = sp.TMutez).layout((("borrow", ("default", "liquidate")), (("repay", "setDelegate"), ("updateState", "withdraw"))))
tprivates = { }
tviews = { }
