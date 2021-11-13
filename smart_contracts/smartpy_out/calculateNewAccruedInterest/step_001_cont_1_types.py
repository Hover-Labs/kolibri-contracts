import smartpy as sp

tstorage = sp.TRecord(lambdaResult = sp.TOption(sp.TNat)).layout("lambdaResult")
tparameter = sp.TVariant(check = sp.TRecord(params = sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))), result = sp.TNat).layout(("params", "result")), test = sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))).layout(("check", "test"))
tglobals = { }
tviews = { }
