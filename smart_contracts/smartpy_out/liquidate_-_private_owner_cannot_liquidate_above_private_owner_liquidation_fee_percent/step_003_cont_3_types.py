import smartpy as sp

tstorage = sp.TRecord(intValue = sp.TInt, natValue = sp.TNat).layout(("intValue", "natValue"))
tparameter = sp.TVariant(default = sp.TUnit, intCallback = sp.TInt, natCallback = sp.TNat).layout(("default", ("intCallback", "natCallback")))
tglobals = { }
tviews = { }
