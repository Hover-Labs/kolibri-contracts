import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), ovenFactoryContractAddress = sp.address('tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98'), ovenMap = {})

  @sp.entry_point
  def addOven(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TAddress))
    sp.verify(sp.sender == self.data.ovenFactoryContractAddress, message = 7)
    self.data.ovenMap[sp.fst(params)] = sp.snd(params)

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.failwith(19)

  @sp.entry_point
  def isOven(self, params):
    sp.verify(self.data.ovenMap.contains(params), message = 1)
    sp.verify(sp.amount == sp.tez(0), message = 15)

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setOvenFactoryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.ovenFactoryContractAddress = params