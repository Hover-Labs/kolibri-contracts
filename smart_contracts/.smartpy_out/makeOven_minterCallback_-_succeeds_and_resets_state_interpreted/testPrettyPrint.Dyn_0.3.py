import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(borrowedTokens = 0, interestIndex = 1, isLiquidated = False, ovenProxyContractAddress = sp.address('tz1c461F8GirBvq5DpFftPoPyCcPR7HQM6gm'), owner = sp.address('tz1S8MNvuFEUsWgjHvi3AxibRBf388NhT1q2'), stabilityFeeTokens = 0)

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.owner, message = 6)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.transfer((sp.self_address, (self.data.owner, (sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * 1000000000000, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, params))))))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))), self.data.ovenProxyContractAddress, entry_point='borrow').open_some())

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.transfer((sp.self_address, (self.data.owner, (sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * 1000000000000, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, self.data.interestIndex)))))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))), self.data.ovenProxyContractAddress, entry_point='deposit').open_some())

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TUnit)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.transfer((sp.self_address, (self.data.owner, (sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * 1000000000000, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, sp.sender))))))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress))))))), self.data.ovenProxyContractAddress, entry_point='liquidate').open_some())

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.owner, message = 6)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.transfer((sp.self_address, (self.data.owner, (sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * 1000000000000, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, params))))))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))), self.data.ovenProxyContractAddress, entry_point='repay').open_some())

  @sp.entry_point
  def setDelegate(self, params):
    sp.set_type(params, sp.TOption(sp.TKeyHash))
    sp.verify(sp.sender == self.data.owner, message = 6)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.set_delegate(params)

  @sp.entry_point
  def updateState(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    sp.verify(sp.fst(params) == sp.self_address, message = 13)
    self.data.borrowedTokens = sp.fst(sp.snd(params))
    self.data.stabilityFeeTokens = sp.fst(sp.snd(sp.snd(params)))
    self.data.interestIndex = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.isLiquidated = sp.snd(sp.snd(sp.snd(sp.snd(params))))

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TMutez)
    sp.verify(sp.sender == self.data.owner, message = 6)
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.transfer((sp.self_address, (self.data.owner, (sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * 1000000000000, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, params))))))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))), self.data.ovenProxyContractAddress, entry_point='withdraw').open_some())