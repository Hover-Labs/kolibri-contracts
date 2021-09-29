import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(administrator = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), balances = {}, debtCeiling = 1000000000000000000000, governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), metadata = {'' : sp.bytes('0x74657a6f732d73746f726167653a64617461'), 'data' : sp.bytes('0x7b206e616d653a2022204b6f6c6962726920546f6b656e20436f6e7472616374222c20226465736372697074696f6e223a20224641312e3220496d706c656d656e746174696f6e206f66206b555344222c2022617574686f72223a2022486f766572204c616273222c2022686f6d6570616765223a20202268747470733a2f2f6b6f6c696272692e66696e616e6365222c2022696e7465726661636573223a205b2022545a49502d3030372d323032312d30312d3239225d207d')}, paused = False, token_metadata = {0 : (0, {'decimals' : sp.bytes('0x3138'), 'icon' : sp.bytes('0x2068747470733a2f2f6b6f6c696272692d646174612e73332e616d617a6f6e6177732e636f6d2f6c6f676f2e706e67'), 'name' : sp.bytes('0x4b6f6c6962726920555344'), 'symbol' : sp.bytes('0x6b555344')})}, totalSupply = 0)

  @sp.entry_point
  def approve(self, params):
    sp.set_type(params, sp.TRecord(spender = sp.TAddress, value = sp.TNat).layout(("spender", "value")))
    sp.verify(~ self.data.paused)
    sp.verify((self.data.balances[sp.sender].approvals.get(params.spender, default_value = 0) == 0) | (params.value == 0), message = 23)
    self.data.balances[sp.sender].approvals[params.spender] = params.value

  @sp.entry_point
  def burn(self, params):
    sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")))
    sp.verify(sp.sender == self.data.administrator, message = 24)
    sp.verify(self.data.balances[params.address].balance >= params.value, message = 23)
    self.data.balances[params.address].balance = sp.as_nat(self.data.balances[params.address].balance - params.value)
    self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)

  @sp.entry_point
  def getAdministrator(self, params):
    sp.set_type(sp.fst(params), sp.TUnit)
    __s13 = sp.local("__s13", self.data.administrator)
    sp.set_type(sp.snd(params), sp.TContract(sp.TAddress))
    sp.transfer(__s13.value, sp.tez(0), sp.snd(params))

  @sp.entry_point
  def getAllowance(self, params):
    __s14 = sp.local("__s14", self.data.balances[sp.fst(params).owner].approvals[sp.fst(params).spender])
    sp.set_type(sp.snd(params), sp.TContract(sp.TNat))
    sp.transfer(__s14.value, sp.tez(0), sp.snd(params))

  @sp.entry_point
  def getBalance(self, params):
    __s15 = sp.local("__s15", self.data.balances[sp.fst(params)].balance)
    sp.set_type(sp.snd(params), sp.TContract(sp.TNat))
    sp.transfer(__s15.value, sp.tez(0), sp.snd(params))

  @sp.entry_point
  def getTotalSupply(self, params):
    sp.set_type(sp.fst(params), sp.TUnit)
    __s16 = sp.local("__s16", self.data.totalSupply)
    sp.set_type(sp.snd(params), sp.TContract(sp.TNat))
    sp.transfer(__s16.value, sp.tez(0), sp.snd(params))

  @sp.entry_point
  def mint(self, params):
    sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")))
    sp.verify(sp.sender == self.data.administrator, message = 24)
    sp.if ~ (self.data.balances.contains(params.address)):
      self.data.balances[params.address] = sp.record(approvals = {}, balance = 0)
    self.data.balances[params.address].balance += params.value
    self.data.totalSupply += params.value
    sp.verify(self.data.totalSupply <= self.data.debtCeiling, message = 20)

  @sp.entry_point
  def setAdministrator(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.administrator = params

  @sp.entry_point
  def setDebtCeiling(self, params):
    sp.set_type(params, sp.TNat)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.debtCeiling = params

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.set_type(params, sp.TAddress)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setPause(self, params):
    sp.set_type(params, sp.TBool)
    sp.verify(sp.sender == self.data.administrator, message = 24)
    self.data.paused = params

  @sp.entry_point
  def transfer(self, params):
    sp.set_type(params, sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))))
    sp.verify((sp.sender == self.data.administrator) | ((~ self.data.paused) & ((params.from_ == sp.sender) | (self.data.balances[params.from_].approvals[sp.sender] >= params.value))), message = 22)
    sp.if ~ (self.data.balances.contains(params.to_)):
      self.data.balances[params.to_] = sp.record(approvals = {}, balance = 0)
    sp.verify(self.data.balances[params.from_].balance >= params.value, message = 23)
    self.data.balances[params.from_].balance = sp.as_nat(self.data.balances[params.from_].balance - params.value)
    self.data.balances[params.to_].balance += params.value
    sp.if (params.from_ != sp.sender) & (~ (sp.sender == self.data.administrator)):
      self.data.balances[params.from_].approvals[sp.sender] = sp.as_nat(self.data.balances[params.from_].approvals[sp.sender] - params.value)

  @sp.entry_point
  def updateContractMetadata(self, params):
    sp.set_type(params, sp.TPair(sp.TString, sp.TBytes))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.metadata[sp.fst(params)] = sp.snd(params)

  @sp.entry_point
  def updateTokenMetadata(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TMap(sp.TString, sp.TBytes)))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.token_metadata[0] = params