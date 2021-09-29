import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(borrowParams = sp.none, governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), liquidateParams = sp.none, minterContractAddress = sp.contract_address(Contract1), oracleContractAddress = sp.contract_address(Contract3), ovenRegistryContractAddress = sp.contract_address(Contract0), pauseGuardianContractAddress = sp.address('tz1LLNkQK4UQV6QcFShiXJ2vT2ELw449MzAA'), paused = True, state = 0, withdrawParams = sp.none)

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, message = 18)
    sp.verify(self.data.state == 0, message = 12)
    self.data.state = 1
    self.data.borrowParams = sp.some(params)
    sp.transfer(sp.self_entry_point('borrow_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def borrow_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, message = 3)
    sp.verify(self.data.state == 1, message = 12)
    sp.transfer((params, self.data.borrowParams.open_some()), sp.balance, sp.contract(sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))), self.data.minterContractAddress, entry_point='borrow').open_some())
    self.data.state = 0
    self.data.borrowParams = sp.none

  @sp.entry_point
  def default(self, params):
    sp.set_type(params, sp.TUnit)
    sp.failwith(19)

  @sp.entry_point
  def deposit(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, message = 18)
    sp.verify(self.data.state == 0, message = 12)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))), self.data.minterContractAddress, entry_point='deposit').open_some())

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, message = 18)
    sp.verify(self.data.state == 0, message = 12)
    self.data.state = 3
    self.data.liquidateParams = sp.some(params)
    sp.transfer(sp.self_entry_point('liquidate_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def liquidate_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, message = 3)
    sp.verify(self.data.state == 3, message = 12)
    sp.transfer((params, self.data.liquidateParams.open_some()), sp.balance, sp.contract(sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))), self.data.minterContractAddress, entry_point='liquidate').open_some())
    self.data.state = 0
    self.data.liquidateParams = sp.none

  @sp.entry_point
  def pause(self, params):
    sp.verify(sp.sender == self.data.pauseGuardianContractAddress, message = 9)
    self.data.paused = True

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, message = 18)
    sp.verify(self.data.state == 0, message = 12)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))), self.data.minterContractAddress, entry_point='repay').open_some())

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setMinterContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.minterContractAddress = params

  @sp.entry_point
  def setOracleContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.oracleContractAddress = params

  @sp.entry_point
  def setOvenRegistryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.ovenRegistryContractAddress = params

  @sp.entry_point
  def setPauseGuardianContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.pauseGuardianContractAddress = params

  @sp.entry_point
  def unpause(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.paused = False

  @sp.entry_point
  def updateState(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))))
    sp.verify(sp.sender == self.data.minterContractAddress, message = 5)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), sp.fst(params), entry_point='updateState').open_some())

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.state == 0, message = 12)
    sp.verify(self.data.paused == False, message = 18)
    self.data.state = 2
    self.data.withdrawParams = sp.some(params)
    sp.transfer(sp.self_entry_point('withdraw_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def withdraw_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, message = 3)
    sp.verify(self.data.state == 2, message = 12)
    sp.transfer((params, self.data.withdrawParams.open_some()), sp.balance, sp.contract(sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez)))))))), self.data.minterContractAddress, entry_point='withdraw').open_some())
    self.data.state = 0
    self.data.withdrawParams = sp.none