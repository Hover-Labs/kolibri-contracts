import smartpy as sp

tstorage = sp.TRecord(minterAddress = sp.TAddress, myOvenAddress = sp.TAddress, ovenFactoryAddress = sp.TAddress, owner = sp.TAddress, state = sp.TIntOrNat, tokensToBorrow = sp.TNat).layout((("minterAddress", ("myOvenAddress", "ovenFactoryAddress")), ("owner", ("state", "tokensToBorrow"))))
tparameter = sp.TVariant(default = sp.TUnit, drain = sp.TMutez, fake_mint = sp.TNat, oven_create = sp.TUnit, set_my_oven_address = sp.TAddress).layout((("default", "drain"), ("fake_mint", ("oven_create", "set_my_oven_address"))))
tprivates = { }
tviews = { }
