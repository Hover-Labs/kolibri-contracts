import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(governorContractAddress = sp.TAddress, initialDelegate = sp.TOption(sp.TKeyHash), makeOvenOwner = sp.TOption(sp.TAddress), minterContractAddress = sp.TAddress, ovenProxyContractAddress = sp.TAddress, ovenRegistryContractAddress = sp.TAddress, state = sp.TIntOrNat).layout((("governorContractAddress", ("initialDelegate", "makeOvenOwner")), (("minterContractAddress", "ovenProxyContractAddress"), ("ovenRegistryContractAddress", "state")))))
    self.init(governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'),
              initialDelegate = sp.some(sp.key_hash('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf')),
              makeOvenOwner = sp.none,
              minterContractAddress = sp.address('KT1Tezooo5zzSmartPyzzSTATiCzzzz48Z4p'),
              ovenProxyContractAddress = sp.address('KT1Tezooo6zzSmartPyzzSTATiCzzztY1196'),
              ovenRegistryContractAddress = sp.address('KT1Tezooo4zzSmartPyzzSTATiCzzzyPVdv3'),
              state = 0)

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.failwith(19)

  @sp.entry_point
  def makeOven(self, params):
    sp.set_type(params, sp.TUnit)
    sp.verify(self.data.state == 0, 12)
    sp.verify(sp.amount == sp.tez(0), 15)
    self.data.state = 1
    self.data.makeOvenOwner = sp.some(sp.sender)
    sp.transfer(sp.self_entry_point('makeOven_minterCallback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.minterContractAddress, entry_point='getInterestIndex').open_some())

  @sp.entry_point
  def makeOven_minterCallback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.minterContractAddress, 5)
    sp.verify(self.data.state == 1, 12)
    create_contract_oven-factory_102 = sp.local("create_contract_oven-factory_102", create contract ...)
    sp.operations().push(create_contract_oven-factory_102.value.operation)
    sp.transfer((create_contract_oven-factory_102.value.address, self.data.makeOvenOwner.open_some()), sp.tez(0), sp.contract(sp.TPair(sp.TAddress, sp.TAddress), self.data.ovenRegistryContractAddress, entry_point='addOven').open_some())
    self.data.state = 0
    self.data.makeOvenOwner = sp.none

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setInitialDelegate(self, params):
    sp.set_type(params, sp.TOption(sp.TKeyHash))
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.initialDelegate = params

  @sp.entry_point
  def setMinterContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.minterContractAddress = params

  @sp.entry_point
  def setOvenProxyContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.ovenProxyContractAddress = params

  @sp.entry_point
  def setOvenRegistryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.ovenRegistryContractAddress = params

sp.add_compilation_target("test", Contract())