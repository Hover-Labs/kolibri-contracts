import smartpy as sp

tstorage = sp.TRecord(administratorContractAddress = sp.TAddress, governorContractAddress = sp.TAddress, ovenRegistryContractAddress = sp.TAddress, savingsAccountContractAddress = sp.TAddress, tokenContractAddress = sp.TAddress).layout((("administratorContractAddress", "governorContractAddress"), ("ovenRegistryContractAddress", ("savingsAccountContractAddress", "tokenContractAddress"))))
tparameter = sp.TVariant(accrueInterest = sp.TNat, default = sp.TUnit, liquidate = sp.TAddress, send = sp.TPair(sp.TMutez, sp.TAddress), sendTokens = sp.TPair(sp.TNat, sp.TAddress), setAdministratorContract = sp.TAddress, setDelegate = sp.TOption(sp.TKeyHash), setGovernorContract = sp.TAddress, setOvenRegistryContract = sp.TAddress, setSavingsAccountContract = sp.TAddress).layout(((("accrueInterest", "default"), ("liquidate", ("send", "sendTokens"))), (("setAdministratorContract", "setDelegate"), ("setGovernorContract", ("setOvenRegistryContract", "setSavingsAccountContract")))))
tglobals = { }
tviews = { }
