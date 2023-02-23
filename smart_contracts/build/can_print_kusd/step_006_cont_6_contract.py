import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(borrowParams = sp.TOption(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))), governorContractAddress = sp.TAddress, liquidateParams = sp.TOption(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))), minterContractAddress = sp.TAddress, oracleContractAddress = sp.TAddress, ovenRegistryContractAddress = sp.TAddress, pauseGuardianContractAddress = sp.TAddress, paused = sp.TBool, state = sp.TIntOrNat, withdrawParams = sp.TOption(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))))).layout(((("borrowParams", "governorContractAddress"), ("liquidateParams", ("minterContractAddress", "oracleContractAddress"))), (("ovenRegistryContractAddress", "pauseGuardianContractAddress"), ("paused", ("state", "withdrawParams"))))))
    self.init(borrowParams = sp.none,
              governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'),
              liquidateParams = sp.none,
              minterContractAddress = sp.address('KT1Tezooo5zzSmartPyzzSTATiCzzzz48Z4p'),
              oracleContractAddress = sp.address('KT1Tezooo3zzSmartPyzzSTATiCzzzseJjWC'),
              ovenRegistryContractAddress = sp.address('KT1Tezooo4zzSmartPyzzSTATiCzzzyPVdv3'),
              pauseGuardianContractAddress = sp.address('tz1LLNkQK4UQV6QcFShiXJ2vT2ELw449MzAA'),
              paused = False,
              state = 0,
              withdrawParams = sp.none)

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, 18)
    sp.verify(self.data.state == 0, 12)
    self.data.state = 1
    self.data.borrowParams = sp.some(params)
    sp.transfer(sp.self_entry_point('borrow_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def borrow_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, 3)
    sp.verify(self.data.state == 1, 12)
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
    sp.verify(self.data.paused == False, 18)
    sp.verify(self.data.state == 0, 12)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))), self.data.minterContractAddress, entry_point='deposit').open_some())

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, 18)
    sp.verify(self.data.state == 0, 12)
    self.data.state = 3
    self.data.liquidateParams = sp.some(params)
    sp.transfer(sp.self_entry_point('liquidate_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def liquidate_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, 3)
    sp.verify(self.data.state == 3, 12)
    sp.transfer((params, self.data.liquidateParams.open_some()), sp.balance, sp.contract(sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))), self.data.minterContractAddress, entry_point='liquidate').open_some())
    self.data.state = 0
    self.data.liquidateParams = sp.none

  @sp.entry_point
  def pause(self):
    sp.verify(sp.sender == self.data.pauseGuardianContractAddress, 9)
    self.data.paused = True

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.paused == False, 18)
    sp.verify(self.data.state == 0, 12)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))), self.data.minterContractAddress, entry_point='repay').open_some())

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setMinterContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.minterContractAddress = params

  @sp.entry_point
  def setOracleContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.oracleContractAddress = params

  @sp.entry_point
  def setOvenRegistryContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.ovenRegistryContractAddress = params

  @sp.entry_point
  def setPauseGuardianContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.pauseGuardianContractAddress = params

  @sp.entry_point
  def unpause(self):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.paused = False

  @sp.entry_point
  def updateState(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))))
    sp.verify(sp.sender == self.data.minterContractAddress, 5)
    sp.transfer(params, sp.amount, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), sp.fst(params), entry_point='updateState').open_some())

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))))
    sp.transfer(sp.sender, sp.tez(0), sp.contract(sp.TAddress, self.data.ovenRegistryContractAddress, entry_point='isOven').open_some())
    sp.verify(self.data.state == 0, 12)
    sp.verify(self.data.paused == False, 18)
    self.data.state = 2
    self.data.withdrawParams = sp.some(params)
    sp.transfer(sp.self_entry_point('withdraw_callback'), sp.tez(0), sp.contract(sp.TContract(sp.TNat), self.data.oracleContractAddress, entry_point='getXtzUsdRate').open_some())

  @sp.entry_point
  def withdraw_callback(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.oracleContractAddress, 3)
    sp.verify(self.data.state == 2, 12)
    sp.transfer((params, self.data.withdrawParams.open_some()), sp.balance, sp.contract(sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez)))))))), self.data.minterContractAddress, entry_point='withdraw').open_some())
    self.data.state = 0
    self.data.withdrawParams = sp.none

sp.add_compilation_target("test", Contract())