import smartpy as sp

tstorage = sp.TRecord(governorContractAddress = sp.TAddress, initialDelegate = sp.TOption(sp.TKeyHash), makeOvenOwner = sp.TOption(sp.TAddress), minterContractAddress = sp.TAddress, ovenProxyContractAddress = sp.TAddress, ovenRegistryContractAddress = sp.TAddress, state = sp.TIntOrNat).layout((("governorContractAddress", ("initialDelegate", "makeOvenOwner")), (("minterContractAddress", "ovenProxyContractAddress"), ("ovenRegistryContractAddress", "state"))))
tparameter = sp.TVariant(default = sp.TUnit, makeOven = sp.TUnit, makeOven_minterCallback = sp.TNat, setGovernorContract = sp.TAddress, setInitialDelegate = sp.TOption(sp.TKeyHash), setMinterContract = sp.TAddress, setOvenProxyContract = sp.TAddress, setOvenRegistryContract = sp.TAddress).layout(((("default", "makeOven"), ("makeOven_minterCallback", "setGovernorContract")), (("setInitialDelegate", "setMinterContract"), ("setOvenProxyContract", "setOvenRegistryContract"))))
tglobals = { }
tviews = { }
