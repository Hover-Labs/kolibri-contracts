import smartpy as sp

tstorage = sp.TRecord(governorContractAddress = sp.TAddress, ovenFactoryContractAddress = sp.TAddress, ovenMap = sp.TBigMap(sp.TAddress, sp.TAddress)).layout(("governorContractAddress", ("ovenFactoryContractAddress", "ovenMap")))
tparameter = sp.TVariant(addOven = sp.TPair(sp.TAddress, sp.TAddress), default = sp.TUnit, isOven = sp.TAddress, setGovernorContract = sp.TAddress, setOvenFactoryContract = sp.TAddress).layout((("addOven", "default"), ("isOven", ("setGovernorContract", "setOvenFactoryContract"))))
tglobals = { }
tviews = { }
