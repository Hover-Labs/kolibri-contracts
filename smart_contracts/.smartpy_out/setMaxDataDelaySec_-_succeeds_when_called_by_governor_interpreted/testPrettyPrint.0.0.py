import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(clientCallback = sp.none, governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), harbingerContractAddress = sp.address('tz1TDSmoZXwVevLTEvKCTHWpomG76oC9S2fJ'), maxDataDelaySec = 30, state = 0)

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.failwith(19)

  @sp.entry_point
  def getXtzUsdRate(self, params):
    sp.set_type(params, sp.TContract(sp.TNat))
    sp.verify(self.data.state == 0, message = 12)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    self.data.state = 1
    self.data.clientCallback = sp.some(sp.to_address(params))
    sp.set_type(sp.self_entry_point('getXtzUsdRate_callback'), sp.TContract(sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat))))
    sp.transfer(('XTZ-USD', sp.self_entry_point('getXtzUsdRate_callback')), sp.tez(0), sp.contract(sp.TPair(sp.TString, sp.TContract(sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat)))), self.data.harbingerContractAddress, entry_point='get').open_some())

  @sp.entry_point
  def getXtzUsdRate_callback(self, params):
    sp.set_type(params, sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat)))
    sp.verify(self.data.state == 1, message = 12)
    sp.verify(sp.sender == self.data.harbingerContractAddress, message = 3)
    sp.verify(sp.fst(params) == 'XTZ-USD', message = 14)
    sp.verify(sp.as_nat(sp.now - sp.fst(sp.snd(params))) < self.data.maxDataDelaySec, message = 17)
    sp.transfer(sp.snd(sp.snd(params)) * 1000000000000, sp.tez(0), sp.contract(sp.TNat, self.data.clientCallback.open_some()).open_some())
    self.data.state = 0
    self.data.clientCallback = sp.none

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setMaxDataDelaySec(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.maxDataDelaySec = params