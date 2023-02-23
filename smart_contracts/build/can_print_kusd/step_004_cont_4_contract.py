import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(governorContractAddress = sp.TAddress, ovenFactoryContractAddress = sp.TAddress, ovenMap = sp.TBigMap(sp.TAddress, sp.TAddress)).layout(("governorContractAddress", ("ovenFactoryContractAddress", "ovenMap"))))
    self.init(governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'),
              ovenFactoryContractAddress = sp.address('tz1irJKkXS2DBWkU1NnmFQx1c1L7pbGg4yhk'),
              ovenMap = {})

  @sp.entry_point
  def addOven(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TAddress))
    sp.verify(sp.sender == self.data.ovenFactoryContractAddress, 7)
    self.data.ovenMap[sp.fst(params)] = sp.snd(params)

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.failwith(19)

  @sp.entry_point
  def isOven(self, params):
    sp.verify(self.data.ovenMap.contains(params), 1)
    sp.verify(sp.amount == sp.tez(0), 15)

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setOvenFactoryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.ovenFactoryContractAddress = params

sp.add_compilation_target("test", Contract())