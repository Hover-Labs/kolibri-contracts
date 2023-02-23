import smartpy as sp

tstorage = sp.TRecord(clientCallback = sp.TOption(sp.TAddress), governorContractAddress = sp.TAddress, harbingerContractAddress = sp.TAddress, maxDataDelaySec = sp.TNat, state = sp.TIntOrNat).layout((("clientCallback", "governorContractAddress"), ("harbingerContractAddress", ("maxDataDelaySec", "state"))))
tparameter = sp.TVariant(default = sp.TUnit, getXtzUsdRate = sp.TContract(sp.TNat), getXtzUsdRate_callback = sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat)), setGovernorContract = sp.TAddress, setMaxDataDelaySec = sp.TNat).layout((("default", "getXtzUsdRate"), ("getXtzUsdRate_callback", ("setGovernorContract", "setMaxDataDelaySec"))))
tglobals = { }
tviews = { }
