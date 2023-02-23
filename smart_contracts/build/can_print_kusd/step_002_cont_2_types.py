import smartpy as sp

tstorage = sp.TRecord(harbingerAsset = sp.TString, harbingerUpdateTime = sp.TTimestamp, harbingerValue = sp.TNat).layout(("harbingerAsset", ("harbingerUpdateTime", "harbingerValue")))
tparameter = sp.TVariant(get = sp.TPair(sp.TString, sp.TContract(sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat)))), setNewPrice = sp.TNat, update = sp.TUnit).layout(("get", ("setNewPrice", "update")))
tprivates = { }
tviews = { }
