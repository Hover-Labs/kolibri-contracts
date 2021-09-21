import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(administratorContractAddress = sp.address('tz1VmiY38m3y95HqQLjMwqnMS7sdMfGomzKi'), governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), ovenRegistryContractAddress = sp.contract_address(Contract0), tokenContractAddress = sp.address('tz1cYufsxHXJcvANhvS55h3aY32a9BAFB494'))

  @sp.entry_point
  def default(self, params):
    pass

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.administratorContractAddress, message = 8)
    sp.transfer(params, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.send(params, sp.tez(0))

  @sp.entry_point
  def send(self, params):
    sp.set_type(params, sp.TPair(sp.TMutez, sp.TAddress))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    sp.send(sp.snd(params), sp.fst(params))

  @sp.entry_point
  def sendTokens(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TAddress))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    sp.transfer(sp.record(from_ = sp.self_address, to_ = sp.snd(params), value = sp.fst(params)), sp.tez(0), sp.contract(sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))), self.data.tokenContractAddress, entry_point='transfer').open_some())

  @sp.entry_point
  def setAdministratorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.administratorContractAddress = params

  @sp.entry_point
  def setDelegate(self, params):
    sp.set_type(params, sp.TOption(sp.TKeyHash))
    sp.verify(sp.sender == self.data.administratorContractAddress, message = 8)
    sp.set_delegate(params)

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setOvenRegistryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.ovenRegistryContractAddress = params