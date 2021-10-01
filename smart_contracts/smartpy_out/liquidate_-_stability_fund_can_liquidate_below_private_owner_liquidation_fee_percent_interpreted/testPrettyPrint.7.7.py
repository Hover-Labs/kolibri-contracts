import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(collateralizationPercentage = 200000000000000000000, devFundSplit = 100000000000000000, developerFundContractAddress = sp.contract_address(Contract4), governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'), interestIndex = 1000000000000000000, lastInterestIndexUpdateTime = sp.timestamp(1601871456), liquidationFeePercent = 80000000000000000, liquidityPoolContractAddress = sp.contract_address(Contract5), ovenProxyContractAddress = sp.contract_address(Contract0), privateOwnerLiquidationThreshold = 25000000000000000000, stabilityFee = 0, stabilityFundContractAddress = sp.contract_address(Contract3), tokenContractAddress = sp.contract_address(Contract2))

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    match_pair_92_fst, match_pair_92_snd = sp.match_tuple(params, names = [ "match_pair_92_fst", "match_pair_92_snd" ])
    match_pair_93_fst, match_pair_93_snd = sp.match_tuple(match_pair_92_snd, names = [ "match_pair_93_fst", "match_pair_93_snd" ])
    match_pair_94_fst, match_pair_94_snd = sp.match_tuple(match_pair_93_snd, names = [ "match_pair_94_fst", "match_pair_94_snd" ])
    match_pair_95_fst, match_pair_95_snd = sp.match_tuple(match_pair_94_snd, names = [ "match_pair_95_fst", "match_pair_95_snd" ])
    match_pair_96_fst, match_pair_96_snd = sp.match_tuple(match_pair_95_snd, names = [ "match_pair_96_fst", "match_pair_96_snd" ])
    match_pair_97_fst, match_pair_97_snd = sp.match_tuple(match_pair_96_snd, names = [ "match_pair_97_fst", "match_pair_97_snd" ])
    match_pair_98_fst, match_pair_98_snd = sp.match_tuple(match_pair_97_snd, names = [ "match_pair_98_fst", "match_pair_98_snd" ])
    sp.set_type(match_pair_92_fst, sp.TNat)
    sp.set_type(match_pair_93_fst, sp.TAddress)
    sp.set_type(match_pair_94_fst, sp.TAddress)
    sp.set_type(match_pair_95_fst, sp.TNat)
    sp.set_type(match_pair_96_fst, sp.TNat)
    sp.set_type(match_pair_97_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_98_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_98_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_98_snd), sp.TNat)
    sp.verify(match_pair_97_fst == False, message = 16)
    sp.set_type(match_pair_96_fst + sp.snd(match_pair_98_snd), sp.TNat)
    sp.set_type((match_pair_96_fst + sp.snd(match_pair_98_snd)) + (sp.as_nat(match_pair_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_98_snd), (match_pair_96_fst, (sp.as_nat(match_pair_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), sp.TNat)
    sp.if ((match_pair_96_fst + sp.snd(match_pair_98_snd)) + (sp.as_nat(match_pair_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_98_snd), (match_pair_96_fst, (sp.as_nat(match_pair_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) > 0:
      sp.verify(self.computeCollateralizationPercentage((match_pair_95_fst, (match_pair_92_fst, (match_pair_96_fst + sp.snd(match_pair_98_snd)) + (sp.as_nat(match_pair_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_98_snd), (match_pair_96_fst, (sp.as_nat(match_pair_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) >= self.data.collateralizationPercentage, message = 11)
    sp.set_type(sp.snd(match_pair_98_snd), sp.TNat)
    sp.set_type(match_pair_94_fst, sp.TAddress)
    sp.transfer(sp.record(address = match_pair_94_fst, value = sp.snd(match_pair_98_snd)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(match_pair_93_fst, sp.TAddress)
    sp.set_type(match_pair_96_fst + sp.snd(match_pair_98_snd), sp.TNat)
    sp.set_type(sp.as_nat(match_pair_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_98_snd), (match_pair_96_fst, (sp.as_nat(match_pair_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_97_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_93_fst, (match_pair_96_fst + sp.snd(match_pair_98_snd), (sp.to_int(sp.as_nat(match_pair_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_98_snd), (match_pair_96_fst, (sp.as_nat(match_pair_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_97_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))

  @sp.entry_point
  def deposit(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    match_pair_222_fst, match_pair_222_snd = sp.match_tuple(params, names = [ "match_pair_222_fst", "match_pair_222_snd" ])
    match_pair_223_fst, match_pair_223_snd = sp.match_tuple(match_pair_222_snd, names = [ "match_pair_223_fst", "match_pair_223_snd" ])
    match_pair_224_fst, match_pair_224_snd = sp.match_tuple(match_pair_223_snd, names = [ "match_pair_224_fst", "match_pair_224_snd" ])
    match_pair_225_fst, match_pair_225_snd = sp.match_tuple(match_pair_224_snd, names = [ "match_pair_225_fst", "match_pair_225_snd" ])
    match_pair_226_fst, match_pair_226_snd = sp.match_tuple(match_pair_225_snd, names = [ "match_pair_226_fst", "match_pair_226_snd" ])
    sp.set_type(match_pair_222_fst, sp.TAddress)
    sp.set_type(match_pair_223_fst, sp.TAddress)
    sp.set_type(match_pair_224_fst, sp.TNat)
    sp.set_type(match_pair_225_fst, sp.TNat)
    sp.set_type(match_pair_226_fst, sp.TBool)
    sp.set_type(sp.as_nat(sp.fst(match_pair_226_snd)), sp.TNat)
    sp.set_type(sp.snd(match_pair_226_snd), sp.TInt)
    sp.verify(match_pair_226_fst == False, message = 16)
    sp.set_type(match_pair_222_fst, sp.TAddress)
    sp.set_type(match_pair_225_fst, sp.TNat)
    sp.set_type(sp.as_nat(sp.fst(match_pair_226_snd)) + self.calculateNewAccruedInterest((sp.snd(match_pair_226_snd), (match_pair_225_fst, (sp.as_nat(sp.fst(match_pair_226_snd)), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_226_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_222_fst, (match_pair_225_fst, (sp.to_int(sp.as_nat(sp.fst(match_pair_226_snd)) + self.calculateNewAccruedInterest((sp.snd(match_pair_226_snd), (match_pair_225_fst, (sp.as_nat(sp.fst(match_pair_226_snd)), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_226_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))

  @sp.entry_point
  def getInterestIndex(self, params):
    sp.set_type(params, sp.TContract(sp.TNat))
    sp.verify(sp.amount == sp.tez(0), message = 15)
    sp.transfer(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.tez(0), params)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    match_pair_326_fst, match_pair_326_snd = sp.match_tuple(params, names = [ "match_pair_326_fst", "match_pair_326_snd" ])
    match_pair_327_fst, match_pair_327_snd = sp.match_tuple(match_pair_326_snd, names = [ "match_pair_327_fst", "match_pair_327_snd" ])
    match_pair_328_fst, match_pair_328_snd = sp.match_tuple(match_pair_327_snd, names = [ "match_pair_328_fst", "match_pair_328_snd" ])
    match_pair_329_fst, match_pair_329_snd = sp.match_tuple(match_pair_328_snd, names = [ "match_pair_329_fst", "match_pair_329_snd" ])
    match_pair_330_fst, match_pair_330_snd = sp.match_tuple(match_pair_329_snd, names = [ "match_pair_330_fst", "match_pair_330_snd" ])
    match_pair_331_fst, match_pair_331_snd = sp.match_tuple(match_pair_330_snd, names = [ "match_pair_331_fst", "match_pair_331_snd" ])
    match_pair_332_fst, match_pair_332_snd = sp.match_tuple(match_pair_331_snd, names = [ "match_pair_332_fst", "match_pair_332_snd" ])
    sp.set_type(match_pair_326_fst, sp.TNat)
    sp.set_type(match_pair_327_fst, sp.TAddress)
    sp.set_type(match_pair_328_fst, sp.TAddress)
    sp.set_type(match_pair_329_fst, sp.TNat)
    sp.set_type(match_pair_330_fst, sp.TNat)
    sp.set_type(match_pair_331_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_332_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_332_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_332_snd), sp.TAddress)
    sp.verify(match_pair_331_fst == False, message = 16)
    sp.verify(self.computeCollateralizationPercentage((match_pair_329_fst, (match_pair_326_fst, match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) < self.data.collateralizationPercentage, message = 10)
    sp.verify(((sp.snd(match_pair_332_snd) == self.data.liquidityPoolContractAddress) | (sp.snd(match_pair_332_snd) == self.data.stabilityFundContractAddress)) | (self.computeCollateralizationPercentage((match_pair_329_fst, (match_pair_326_fst, match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) < sp.as_nat(self.data.collateralizationPercentage - self.data.privateOwnerLiquidationThreshold)), message = 26)
    sp.set_type((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000), sp.TNat)
    sp.set_type(sp.snd(match_pair_332_snd), sp.TAddress)
    sp.transfer(sp.record(address = sp.snd(match_pair_332_snd), value = (match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='burn').open_some())
    sp.set_type((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000), sp.TNat)
    sp.set_type((((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000, sp.TNat)
    sp.set_type(self.data.developerFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.developerFundContractAddress, value = (((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.as_nat(((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) - ((((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000)), sp.TNat)
    sp.set_type(self.data.stabilityFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.stabilityFundContractAddress, value = sp.as_nat(((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) - ((((sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_330_fst + (sp.as_nat(match_pair_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_332_snd), (match_pair_330_fst, (sp.as_nat(match_pair_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000))), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.send(sp.snd(match_pair_332_snd), sp.mutez(match_pair_329_fst // 1000000000000))
    sp.set_type(match_pair_327_fst, sp.TAddress)
    sp.set_type(0, sp.TNat)
    sp.set_type(0, sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(True, sp.TBool)
    sp.set_type(sp.tez(0), sp.TMutez)
    sp.transfer((match_pair_327_fst, (0, (sp.to_int(0), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), True)))), sp.tez(0), sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    match_pair_156_fst, match_pair_156_snd = sp.match_tuple(params, names = [ "match_pair_156_fst", "match_pair_156_snd" ])
    match_pair_157_fst, match_pair_157_snd = sp.match_tuple(match_pair_156_snd, names = [ "match_pair_157_fst", "match_pair_157_snd" ])
    match_pair_158_fst, match_pair_158_snd = sp.match_tuple(match_pair_157_snd, names = [ "match_pair_158_fst", "match_pair_158_snd" ])
    match_pair_159_fst, match_pair_159_snd = sp.match_tuple(match_pair_158_snd, names = [ "match_pair_159_fst", "match_pair_159_snd" ])
    match_pair_160_fst, match_pair_160_snd = sp.match_tuple(match_pair_159_snd, names = [ "match_pair_160_fst", "match_pair_160_snd" ])
    match_pair_161_fst, match_pair_161_snd = sp.match_tuple(match_pair_160_snd, names = [ "match_pair_161_fst", "match_pair_161_snd" ])
    sp.set_type(match_pair_156_fst, sp.TAddress)
    sp.set_type(match_pair_157_fst, sp.TAddress)
    sp.set_type(match_pair_158_fst, sp.TNat)
    sp.set_type(match_pair_159_fst, sp.TNat)
    sp.set_type(match_pair_160_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_161_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_161_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_161_snd), sp.TNat)
    sp.verify(match_pair_160_fst == False, message = 16)
    stabilityFeeTokensRepaid = sp.local("stabilityFeeTokensRepaid", 0)
    remainingStabilityFeeTokens = sp.local("remainingStabilityFeeTokens", 0)
    remainingBorrowedTokenBalance = sp.local("remainingBorrowedTokenBalance", 0)
    sp.if sp.snd(match_pair_161_snd) < (sp.as_nat(match_pair_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_161_snd), (match_pair_159_fst, (sp.as_nat(match_pair_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))):
      stabilityFeeTokensRepaid.value = sp.snd(match_pair_161_snd)
      remainingStabilityFeeTokens.value = sp.as_nat((sp.as_nat(match_pair_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_161_snd), (match_pair_159_fst, (sp.as_nat(match_pair_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) - sp.snd(match_pair_161_snd))
      remainingBorrowedTokenBalance.value = match_pair_159_fst
    sp.else:
      stabilityFeeTokensRepaid.value = sp.as_nat(match_pair_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_161_snd), (match_pair_159_fst, (sp.as_nat(match_pair_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))
      remainingStabilityFeeTokens.value = 0
      remainingBorrowedTokenBalance.value = sp.as_nat(match_pair_159_fst - sp.as_nat(sp.snd(match_pair_161_snd) - (sp.as_nat(match_pair_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_161_snd), (match_pair_159_fst, (sp.as_nat(match_pair_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))
    sp.set_type(stabilityFeeTokensRepaid.value, sp.TNat)
    sp.set_type((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000, sp.TNat)
    sp.set_type(self.data.developerFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.developerFundContractAddress, value = (stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.as_nat(stabilityFeeTokensRepaid.value - ((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000)), sp.TNat)
    sp.set_type(self.data.stabilityFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.stabilityFundContractAddress, value = sp.as_nat(stabilityFeeTokensRepaid.value - ((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000))), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.snd(match_pair_161_snd), sp.TNat)
    sp.set_type(match_pair_157_fst, sp.TAddress)
    sp.transfer(sp.record(address = match_pair_157_fst, value = sp.snd(match_pair_161_snd)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='burn').open_some())
    sp.set_type(match_pair_156_fst, sp.TAddress)
    sp.set_type(remainingBorrowedTokenBalance.value, sp.TNat)
    sp.set_type(remainingStabilityFeeTokens.value, sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_160_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_156_fst, (remainingBorrowedTokenBalance.value, (sp.to_int(remainingStabilityFeeTokens.value), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_160_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))

  @sp.entry_point
  def setCollateralizationPercentage(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.collateralizationPercentage = params
    self.data.privateOwnerLiquidationThreshold = sp.as_nat(params - self.data.privateOwnerLiquidationThreshold)

  @sp.entry_point
  def setDeveloperFundContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.developerFundContractAddress = params

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setLiquidationFeePercent(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.liquidationFeePercent = params

  @sp.entry_point
  def setLiquidityPoolContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.liquidityPoolContractAddress = params

  @sp.entry_point
  def setOvenProxyContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.ovenProxyContractAddress = params

  @sp.entry_point
  def setPrivateLiquidationThreshold(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.privateOwnerLiquidationThreshold = params

  @sp.entry_point
  def setStabilityFee(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    self.data.stabilityFee = params

  @sp.entry_point
  def setStabilityFundContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.stabilityFundContractAddress = params

  @sp.entry_point
  def setTokenContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.tokenContractAddress = params

  @sp.entry_point
  def updateContracts(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TAddress)))))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    match_pair_459_fst, match_pair_459_snd = sp.match_tuple(params, names = [ "match_pair_459_fst", "match_pair_459_snd" ])
    match_pair_460_fst, match_pair_460_snd = sp.match_tuple(match_pair_459_snd, names = [ "match_pair_460_fst", "match_pair_460_snd" ])
    match_pair_461_fst, match_pair_461_snd = sp.match_tuple(match_pair_460_snd, names = [ "match_pair_461_fst", "match_pair_461_snd" ])
    match_pair_462_fst, match_pair_462_snd = sp.match_tuple(match_pair_461_snd, names = [ "match_pair_462_fst", "match_pair_462_snd" ])
    self.data.governorContractAddress = match_pair_459_fst
    self.data.tokenContractAddress = match_pair_460_fst
    self.data.ovenProxyContractAddress = match_pair_461_fst
    self.data.stabilityFundContractAddress = match_pair_462_fst
    self.data.developerFundContractAddress = match_pair_462_snd

  @sp.entry_point
  def updateFundSplits(self, params):
    sp.set_type(params, sp.TRecord(developerFundSplit = sp.TNat, stabilityFundSplit = sp.TNat).layout(("developerFundSplit", "stabilityFundSplit")))
    sp.verify((params.developerFundSplit + params.stabilityFundSplit) == 1000000000000000000, message = 25)
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.devFundSplit = params.developerFundSplit

  @sp.entry_point
  def updateParams(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TOption(sp.TMutez)))))
    sp.verify(sp.sender == self.data.governorContractAddress, message = 4)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    match_pair_419_fst, match_pair_419_snd = sp.match_tuple(params, names = [ "match_pair_419_fst", "match_pair_419_snd" ])
    match_pair_420_fst, match_pair_420_snd = sp.match_tuple(match_pair_419_snd, names = [ "match_pair_420_fst", "match_pair_420_snd" ])
    self.data.stabilityFee = match_pair_419_fst
    self.data.liquidationFeePercent = match_pair_420_fst
    self.data.collateralizationPercentage = sp.fst(match_pair_420_snd)

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = 2)
    match_pair_267_fst, match_pair_267_snd = sp.match_tuple(params, names = [ "match_pair_267_fst", "match_pair_267_snd" ])
    match_pair_268_fst, match_pair_268_snd = sp.match_tuple(match_pair_267_snd, names = [ "match_pair_268_fst", "match_pair_268_snd" ])
    match_pair_269_fst, match_pair_269_snd = sp.match_tuple(match_pair_268_snd, names = [ "match_pair_269_fst", "match_pair_269_snd" ])
    match_pair_270_fst, match_pair_270_snd = sp.match_tuple(match_pair_269_snd, names = [ "match_pair_270_fst", "match_pair_270_snd" ])
    match_pair_271_fst, match_pair_271_snd = sp.match_tuple(match_pair_270_snd, names = [ "match_pair_271_fst", "match_pair_271_snd" ])
    match_pair_272_fst, match_pair_272_snd = sp.match_tuple(match_pair_271_snd, names = [ "match_pair_272_fst", "match_pair_272_snd" ])
    match_pair_273_fst, match_pair_273_snd = sp.match_tuple(match_pair_272_snd, names = [ "match_pair_273_fst", "match_pair_273_snd" ])
    sp.set_type(match_pair_267_fst, sp.TNat)
    sp.set_type(match_pair_268_fst, sp.TAddress)
    sp.set_type(match_pair_269_fst, sp.TAddress)
    sp.set_type(match_pair_270_fst, sp.TNat)
    sp.set_type(match_pair_271_fst, sp.TNat)
    sp.set_type(match_pair_272_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_273_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_273_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_273_snd), sp.TMutez)
    sp.if (match_pair_271_fst + (sp.as_nat(match_pair_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_273_snd), (match_pair_271_fst, (sp.as_nat(match_pair_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) > 0:
      sp.verify(self.computeCollateralizationPercentage((sp.as_nat(match_pair_270_fst - (sp.fst(sp.ediv(sp.snd(match_pair_273_snd), sp.mutez(1)).open_some()) * 1000000000000)), (match_pair_267_fst, match_pair_271_fst + (sp.as_nat(match_pair_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_273_snd), (match_pair_271_fst, (sp.as_nat(match_pair_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) >= self.data.collateralizationPercentage, message = 11)
    sp.send(match_pair_269_fst, sp.snd(match_pair_273_snd))
    sp.set_type(match_pair_268_fst, sp.TAddress)
    sp.set_type(match_pair_271_fst, sp.TNat)
    sp.set_type(sp.as_nat(match_pair_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_273_snd), (match_pair_271_fst, (sp.as_nat(match_pair_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_272_fst, sp.TBool)
    sp.set_type(sp.mutez(match_pair_270_fst // 1000000000000) - sp.snd(match_pair_273_snd), sp.TMutez)
    sp.transfer((match_pair_268_fst, (match_pair_271_fst, (sp.to_int(sp.as_nat(match_pair_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_273_snd), (match_pair_271_fst, (sp.as_nat(match_pair_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_272_fst)))), sp.mutez(match_pair_270_fst // 1000000000000) - sp.snd(match_pair_273_snd), sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))