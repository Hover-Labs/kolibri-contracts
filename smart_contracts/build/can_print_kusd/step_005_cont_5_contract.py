import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(collateralizationPercentage = sp.TNat, devFundSplit = sp.TNat, developerFundContractAddress = sp.TAddress, governorContractAddress = sp.TAddress, interestIndex = sp.TNat, lastInterestIndexUpdateTime = sp.TTimestamp, liquidationFeePercent = sp.TNat, liquidityPoolContractAddress = sp.TAddress, ovenProxyContractAddress = sp.TAddress, privateOwnerLiquidationThreshold = sp.TNat, stabilityFee = sp.TNat, stabilityFundContractAddress = sp.TAddress, tokenContractAddress = sp.TAddress).layout(((("collateralizationPercentage", ("devFundSplit", "developerFundContractAddress")), ("governorContractAddress", ("interestIndex", "lastInterestIndexUpdateTime"))), (("liquidationFeePercent", ("liquidityPoolContractAddress", "ovenProxyContractAddress")), (("privateOwnerLiquidationThreshold", "stabilityFee"), ("stabilityFundContractAddress", "tokenContractAddress"))))))
    self.init(collateralizationPercentage = 200000000000000000000,
              devFundSplit = 100000000000000000,
              developerFundContractAddress = sp.address('tz1R6Ej25VSerE3MkSoEEeBjKHCDTFbpKuSX'),
              governorContractAddress = sp.address('tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf'),
              interestIndex = 1000000000000000000,
              lastInterestIndexUpdateTime = sp.timestamp(0),
              liquidationFeePercent = 80000000000000000,
              liquidityPoolContractAddress = sp.address('tz3QSGPoRp3Kn7n3vY24eYeu3Peuqo45LQ4D'),
              ovenProxyContractAddress = sp.address('tz1c461F8GirBvq5DpFftPoPyCcPR7HQM6gm'),
              privateOwnerLiquidationThreshold = 20000000000000000000,
              stabilityFee = 0,
              stabilityFundContractAddress = sp.address('tz1W5VkdB5s7ENMESVBtwyt9kyvLqPcUczRT'),
              tokenContractAddress = sp.address('tz1cYufsxHXJcvANhvS55h3aY32a9BAFB494'))

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, 2)
    match_pair_minter_92_fst, match_pair_minter_92_snd = sp.match_tuple(params, "match_pair_minter_92_fst", "match_pair_minter_92_snd")
    match_pair_minter_93_fst, match_pair_minter_93_snd = sp.match_tuple(match_pair_minter_92_snd, "match_pair_minter_93_fst", "match_pair_minter_93_snd")
    match_pair_minter_94_fst, match_pair_minter_94_snd = sp.match_tuple(match_pair_minter_93_snd, "match_pair_minter_94_fst", "match_pair_minter_94_snd")
    match_pair_minter_95_fst, match_pair_minter_95_snd = sp.match_tuple(match_pair_minter_94_snd, "match_pair_minter_95_fst", "match_pair_minter_95_snd")
    match_pair_minter_96_fst, match_pair_minter_96_snd = sp.match_tuple(match_pair_minter_95_snd, "match_pair_minter_96_fst", "match_pair_minter_96_snd")
    match_pair_minter_97_fst, match_pair_minter_97_snd = sp.match_tuple(match_pair_minter_96_snd, "match_pair_minter_97_fst", "match_pair_minter_97_snd")
    match_pair_minter_98_fst, match_pair_minter_98_snd = sp.match_tuple(match_pair_minter_97_snd, "match_pair_minter_98_fst", "match_pair_minter_98_snd")
    sp.set_type(match_pair_minter_92_fst, sp.TNat)
    sp.set_type(match_pair_minter_93_fst, sp.TAddress)
    sp.set_type(match_pair_minter_94_fst, sp.TAddress)
    sp.set_type(match_pair_minter_95_fst, sp.TNat)
    sp.set_type(match_pair_minter_96_fst, sp.TNat)
    sp.set_type(match_pair_minter_97_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_minter_98_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_minter_98_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_minter_98_snd), sp.TNat)
    sp.verify(match_pair_minter_97_fst == False, 16)
    sp.set_type(match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd), sp.TNat)
    sp.set_type((match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd)) + (sp.as_nat(match_pair_minter_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_98_snd), (match_pair_minter_96_fst, (sp.as_nat(match_pair_minter_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), sp.TNat)
    sp.if ((match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd)) + (sp.as_nat(match_pair_minter_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_98_snd), (match_pair_minter_96_fst, (sp.as_nat(match_pair_minter_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) > 0:
      sp.verify(self.computeCollateralizationPercentage((match_pair_minter_95_fst, (match_pair_minter_92_fst, (match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd)) + (sp.as_nat(match_pair_minter_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_98_snd), (match_pair_minter_96_fst, (sp.as_nat(match_pair_minter_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) >= self.data.collateralizationPercentage, 11)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.set_type(match_pair_minter_93_fst, sp.TAddress)
    sp.set_type(match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd), sp.TNat)
    sp.set_type(sp.as_nat(match_pair_minter_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_98_snd), (match_pair_minter_96_fst, (sp.as_nat(match_pair_minter_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_minter_97_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_minter_93_fst, (match_pair_minter_96_fst + sp.snd(match_pair_minter_98_snd), (sp.to_int(sp.as_nat(match_pair_minter_98_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_98_snd), (match_pair_minter_96_fst, (sp.as_nat(match_pair_minter_98_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_minter_97_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    sp.set_type(sp.snd(match_pair_minter_98_snd), sp.TNat)
    sp.set_type(match_pair_minter_94_fst, sp.TAddress)
    sp.transfer(sp.record(address = match_pair_minter_94_fst, value = sp.snd(match_pair_minter_98_snd)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())

  @sp.entry_point
  def deposit(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, 2)
    match_pair_minter_222_fst, match_pair_minter_222_snd = sp.match_tuple(params, "match_pair_minter_222_fst", "match_pair_minter_222_snd")
    match_pair_minter_223_fst, match_pair_minter_223_snd = sp.match_tuple(match_pair_minter_222_snd, "match_pair_minter_223_fst", "match_pair_minter_223_snd")
    match_pair_minter_224_fst, match_pair_minter_224_snd = sp.match_tuple(match_pair_minter_223_snd, "match_pair_minter_224_fst", "match_pair_minter_224_snd")
    match_pair_minter_225_fst, match_pair_minter_225_snd = sp.match_tuple(match_pair_minter_224_snd, "match_pair_minter_225_fst", "match_pair_minter_225_snd")
    match_pair_minter_226_fst, match_pair_minter_226_snd = sp.match_tuple(match_pair_minter_225_snd, "match_pair_minter_226_fst", "match_pair_minter_226_snd")
    sp.set_type(match_pair_minter_222_fst, sp.TAddress)
    sp.set_type(match_pair_minter_223_fst, sp.TAddress)
    sp.set_type(match_pair_minter_224_fst, sp.TNat)
    sp.set_type(match_pair_minter_225_fst, sp.TNat)
    sp.set_type(match_pair_minter_226_fst, sp.TBool)
    sp.set_type(sp.as_nat(sp.fst(match_pair_minter_226_snd)), sp.TNat)
    sp.set_type(sp.snd(match_pair_minter_226_snd), sp.TInt)
    sp.verify(match_pair_minter_226_fst == False, 16)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.set_type(match_pair_minter_222_fst, sp.TAddress)
    sp.set_type(match_pair_minter_225_fst, sp.TNat)
    sp.set_type(sp.as_nat(sp.fst(match_pair_minter_226_snd)) + self.calculateNewAccruedInterest((sp.snd(match_pair_minter_226_snd), (match_pair_minter_225_fst, (sp.as_nat(sp.fst(match_pair_minter_226_snd)), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_minter_226_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_minter_222_fst, (match_pair_minter_225_fst, (sp.to_int(sp.as_nat(sp.fst(match_pair_minter_226_snd)) + self.calculateNewAccruedInterest((sp.snd(match_pair_minter_226_snd), (match_pair_minter_225_fst, (sp.as_nat(sp.fst(match_pair_minter_226_snd)), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_minter_226_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())

  @sp.entry_point
  def getInterestIndex(self, params):
    sp.set_type(params, sp.TContract(sp.TNat))
    sp.verify(sp.amount == sp.tez(0), 15)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.transfer(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.tez(0), params)

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, 2)
    match_pair_minter_326_fst, match_pair_minter_326_snd = sp.match_tuple(params, "match_pair_minter_326_fst", "match_pair_minter_326_snd")
    match_pair_minter_327_fst, match_pair_minter_327_snd = sp.match_tuple(match_pair_minter_326_snd, "match_pair_minter_327_fst", "match_pair_minter_327_snd")
    match_pair_minter_328_fst, match_pair_minter_328_snd = sp.match_tuple(match_pair_minter_327_snd, "match_pair_minter_328_fst", "match_pair_minter_328_snd")
    match_pair_minter_329_fst, match_pair_minter_329_snd = sp.match_tuple(match_pair_minter_328_snd, "match_pair_minter_329_fst", "match_pair_minter_329_snd")
    match_pair_minter_330_fst, match_pair_minter_330_snd = sp.match_tuple(match_pair_minter_329_snd, "match_pair_minter_330_fst", "match_pair_minter_330_snd")
    match_pair_minter_331_fst, match_pair_minter_331_snd = sp.match_tuple(match_pair_minter_330_snd, "match_pair_minter_331_fst", "match_pair_minter_331_snd")
    match_pair_minter_332_fst, match_pair_minter_332_snd = sp.match_tuple(match_pair_minter_331_snd, "match_pair_minter_332_fst", "match_pair_minter_332_snd")
    sp.set_type(match_pair_minter_326_fst, sp.TNat)
    sp.set_type(match_pair_minter_327_fst, sp.TAddress)
    sp.set_type(match_pair_minter_328_fst, sp.TAddress)
    sp.set_type(match_pair_minter_329_fst, sp.TNat)
    sp.set_type(match_pair_minter_330_fst, sp.TNat)
    sp.set_type(match_pair_minter_331_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_minter_332_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_minter_332_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_minter_332_snd), sp.TAddress)
    sp.verify(match_pair_minter_331_fst == False, 16)
    sp.verify(self.computeCollateralizationPercentage((match_pair_minter_329_fst, (match_pair_minter_326_fst, match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) < self.data.collateralizationPercentage, 10)
    sp.verify(((sp.snd(match_pair_minter_332_snd) == self.data.liquidityPoolContractAddress) | (sp.snd(match_pair_minter_332_snd) == self.data.stabilityFundContractAddress)) | (self.computeCollateralizationPercentage((match_pair_minter_329_fst, (match_pair_minter_326_fst, match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) < sp.as_nat(self.data.collateralizationPercentage - self.data.privateOwnerLiquidationThreshold)), 26)
    sp.set_type((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000), sp.TNat)
    sp.set_type(sp.snd(match_pair_minter_332_snd), sp.TAddress)
    sp.transfer(sp.record(address = sp.snd(match_pair_minter_332_snd), value = (match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='burn').open_some())
    sp.set_type((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000), sp.TNat)
    sp.set_type((((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000, sp.TNat)
    sp.set_type(self.data.developerFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.developerFundContractAddress, value = (((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.as_nat(((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) - ((((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000)), sp.TNat)
    sp.set_type(self.data.stabilityFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.stabilityFundContractAddress, value = sp.as_nat(((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) - ((((sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) + (((match_pair_minter_330_fst + (sp.as_nat(match_pair_minter_332_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_332_snd), (match_pair_minter_330_fst, (sp.as_nat(match_pair_minter_332_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) * self.data.liquidationFeePercent) // 1000000000000000000)) * self.data.devFundSplit) // 1000000000000000000))), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.set_type(match_pair_minter_327_fst, sp.TAddress)
    sp.set_type(0, sp.TNat)
    sp.set_type(0, sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(True, sp.TBool)
    sp.set_type(sp.tez(0), sp.TMutez)
    sp.transfer((match_pair_minter_327_fst, (0, (sp.to_int(0), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), True)))), sp.tez(0), sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    sp.send(sp.snd(match_pair_minter_332_snd), sp.mul(match_pair_minter_329_fst // 1000000000000, sp.mutez(1)))

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, 2)
    match_pair_minter_156_fst, match_pair_minter_156_snd = sp.match_tuple(params, "match_pair_minter_156_fst", "match_pair_minter_156_snd")
    match_pair_minter_157_fst, match_pair_minter_157_snd = sp.match_tuple(match_pair_minter_156_snd, "match_pair_minter_157_fst", "match_pair_minter_157_snd")
    match_pair_minter_158_fst, match_pair_minter_158_snd = sp.match_tuple(match_pair_minter_157_snd, "match_pair_minter_158_fst", "match_pair_minter_158_snd")
    match_pair_minter_159_fst, match_pair_minter_159_snd = sp.match_tuple(match_pair_minter_158_snd, "match_pair_minter_159_fst", "match_pair_minter_159_snd")
    match_pair_minter_160_fst, match_pair_minter_160_snd = sp.match_tuple(match_pair_minter_159_snd, "match_pair_minter_160_fst", "match_pair_minter_160_snd")
    match_pair_minter_161_fst, match_pair_minter_161_snd = sp.match_tuple(match_pair_minter_160_snd, "match_pair_minter_161_fst", "match_pair_minter_161_snd")
    sp.set_type(match_pair_minter_156_fst, sp.TAddress)
    sp.set_type(match_pair_minter_157_fst, sp.TAddress)
    sp.set_type(match_pair_minter_158_fst, sp.TNat)
    sp.set_type(match_pair_minter_159_fst, sp.TNat)
    sp.set_type(match_pair_minter_160_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_minter_161_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_minter_161_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_minter_161_snd), sp.TNat)
    sp.verify(match_pair_minter_160_fst == False, 16)
    stabilityFeeTokensRepaid = sp.local("stabilityFeeTokensRepaid", 0)
    remainingStabilityFeeTokens = sp.local("remainingStabilityFeeTokens", 0)
    remainingBorrowedTokenBalance = sp.local("remainingBorrowedTokenBalance", 0)
    sp.if sp.snd(match_pair_minter_161_snd) < (sp.as_nat(match_pair_minter_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_161_snd), (match_pair_minter_159_fst, (sp.as_nat(match_pair_minter_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))):
      stabilityFeeTokensRepaid.value = sp.snd(match_pair_minter_161_snd)
      remainingStabilityFeeTokens.value = sp.as_nat((sp.as_nat(match_pair_minter_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_161_snd), (match_pair_minter_159_fst, (sp.as_nat(match_pair_minter_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))) - sp.snd(match_pair_minter_161_snd))
      remainingBorrowedTokenBalance.value = match_pair_minter_159_fst
    sp.else:
      stabilityFeeTokensRepaid.value = sp.as_nat(match_pair_minter_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_161_snd), (match_pair_minter_159_fst, (sp.as_nat(match_pair_minter_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))
      remainingStabilityFeeTokens.value = 0
      remainingBorrowedTokenBalance.value = sp.as_nat(match_pair_minter_159_fst - sp.as_nat(sp.snd(match_pair_minter_161_snd) - (sp.as_nat(match_pair_minter_161_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_161_snd), (match_pair_minter_159_fst, (sp.as_nat(match_pair_minter_161_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.set_type(match_pair_minter_156_fst, sp.TAddress)
    sp.set_type(remainingBorrowedTokenBalance.value, sp.TNat)
    sp.set_type(remainingStabilityFeeTokens.value, sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_minter_160_fst, sp.TBool)
    sp.set_type(sp.balance, sp.TMutez)
    sp.transfer((match_pair_minter_156_fst, (remainingBorrowedTokenBalance.value, (sp.to_int(remainingStabilityFeeTokens.value), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_minter_160_fst)))), sp.balance, sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    sp.set_type(stabilityFeeTokensRepaid.value, sp.TNat)
    sp.set_type((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000, sp.TNat)
    sp.set_type(self.data.developerFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.developerFundContractAddress, value = (stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.as_nat(stabilityFeeTokensRepaid.value - ((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000)), sp.TNat)
    sp.set_type(self.data.stabilityFundContractAddress, sp.TAddress)
    sp.transfer(sp.record(address = self.data.stabilityFundContractAddress, value = sp.as_nat(stabilityFeeTokensRepaid.value - ((stabilityFeeTokensRepaid.value * self.data.devFundSplit) // 1000000000000000000))), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='mint').open_some())
    sp.set_type(sp.snd(match_pair_minter_161_snd), sp.TNat)
    sp.set_type(match_pair_minter_157_fst, sp.TAddress)
    sp.transfer(sp.record(address = match_pair_minter_157_fst, value = sp.snd(match_pair_minter_161_snd)), sp.tez(0), sp.contract(sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")), self.data.tokenContractAddress, entry_point='burn').open_some())

  @sp.entry_point
  def setCollateralizationPercentage(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.collateralizationPercentage = params

  @sp.entry_point
  def setDeveloperFundContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.developerFundContractAddress = params

  @sp.entry_point
  def setGovernorContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.governorContractAddress = params

  @sp.entry_point
  def setLiquidationFeePercent(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.liquidationFeePercent = params

  @sp.entry_point
  def setLiquidityPoolContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.liquidityPoolContractAddress = params

  @sp.entry_point
  def setOvenProxyContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.ovenProxyContractAddress = params

  @sp.entry_point
  def setPrivateLiquidationThreshold(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.privateOwnerLiquidationThreshold = params

  @sp.entry_point
  def setStabilityFee(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    self.data.stabilityFee = params

  @sp.entry_point
  def setStabilityFundContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.stabilityFundContractAddress = params

  @sp.entry_point
  def setTokenContract(self, params):
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.tokenContractAddress = params

  @sp.entry_point
  def updateContracts(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TAddress)))))
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    match_pair_minter_458_fst, match_pair_minter_458_snd = sp.match_tuple(params, "match_pair_minter_458_fst", "match_pair_minter_458_snd")
    match_pair_minter_459_fst, match_pair_minter_459_snd = sp.match_tuple(match_pair_minter_458_snd, "match_pair_minter_459_fst", "match_pair_minter_459_snd")
    match_pair_minter_460_fst, match_pair_minter_460_snd = sp.match_tuple(match_pair_minter_459_snd, "match_pair_minter_460_fst", "match_pair_minter_460_snd")
    match_pair_minter_461_fst, match_pair_minter_461_snd = sp.match_tuple(match_pair_minter_460_snd, "match_pair_minter_461_fst", "match_pair_minter_461_snd")
    self.data.governorContractAddress = match_pair_minter_458_fst
    self.data.tokenContractAddress = match_pair_minter_459_fst
    self.data.ovenProxyContractAddress = match_pair_minter_460_fst
    self.data.stabilityFundContractAddress = match_pair_minter_461_fst
    self.data.developerFundContractAddress = match_pair_minter_461_snd

  @sp.entry_point
  def updateFundSplits(self, params):
    sp.set_type(params, sp.TRecord(developerFundSplit = sp.TNat, stabilityFundSplit = sp.TNat).layout(("developerFundSplit", "stabilityFundSplit")))
    sp.verify((params.developerFundSplit + params.stabilityFundSplit) == 1000000000000000000, 25)
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.devFundSplit = params.developerFundSplit

  @sp.entry_point
  def updateParams(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TOption(sp.TMutez)))))
    sp.verify(sp.sender == self.data.governorContractAddress, 4)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    match_pair_minter_419_fst, match_pair_minter_419_snd = sp.match_tuple(params, "match_pair_minter_419_fst", "match_pair_minter_419_snd")
    match_pair_minter_420_fst, match_pair_minter_420_snd = sp.match_tuple(match_pair_minter_419_snd, "match_pair_minter_420_fst", "match_pair_minter_420_snd")
    self.data.stabilityFee = match_pair_minter_419_fst
    self.data.liquidationFeePercent = match_pair_minter_420_fst
    self.data.collateralizationPercentage = sp.fst(match_pair_minter_420_snd)

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez)))))))))
    sp.verify(sp.sender == self.data.ovenProxyContractAddress, 2)
    match_pair_minter_267_fst, match_pair_minter_267_snd = sp.match_tuple(params, "match_pair_minter_267_fst", "match_pair_minter_267_snd")
    match_pair_minter_268_fst, match_pair_minter_268_snd = sp.match_tuple(match_pair_minter_267_snd, "match_pair_minter_268_fst", "match_pair_minter_268_snd")
    match_pair_minter_269_fst, match_pair_minter_269_snd = sp.match_tuple(match_pair_minter_268_snd, "match_pair_minter_269_fst", "match_pair_minter_269_snd")
    match_pair_minter_270_fst, match_pair_minter_270_snd = sp.match_tuple(match_pair_minter_269_snd, "match_pair_minter_270_fst", "match_pair_minter_270_snd")
    match_pair_minter_271_fst, match_pair_minter_271_snd = sp.match_tuple(match_pair_minter_270_snd, "match_pair_minter_271_fst", "match_pair_minter_271_snd")
    match_pair_minter_272_fst, match_pair_minter_272_snd = sp.match_tuple(match_pair_minter_271_snd, "match_pair_minter_272_fst", "match_pair_minter_272_snd")
    match_pair_minter_273_fst, match_pair_minter_273_snd = sp.match_tuple(match_pair_minter_272_snd, "match_pair_minter_273_fst", "match_pair_minter_273_snd")
    sp.set_type(match_pair_minter_267_fst, sp.TNat)
    sp.set_type(match_pair_minter_268_fst, sp.TAddress)
    sp.set_type(match_pair_minter_269_fst, sp.TAddress)
    sp.set_type(match_pair_minter_270_fst, sp.TNat)
    sp.set_type(match_pair_minter_271_fst, sp.TNat)
    sp.set_type(match_pair_minter_272_fst, sp.TBool)
    sp.set_type(sp.as_nat(match_pair_minter_273_fst), sp.TNat)
    sp.set_type(sp.fst(match_pair_minter_273_snd), sp.TInt)
    sp.set_type(sp.snd(match_pair_minter_273_snd), sp.TMutez)
    sp.if (match_pair_minter_271_fst + (sp.as_nat(match_pair_minter_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_273_snd), (match_pair_minter_271_fst, (sp.as_nat(match_pair_minter_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))) > 0:
      sp.verify(self.computeCollateralizationPercentage((sp.as_nat(match_pair_minter_270_fst - (sp.fst(sp.ediv(sp.snd(match_pair_minter_273_snd), sp.mutez(1)).open_some()) * 1000000000000)), (match_pair_minter_267_fst, match_pair_minter_271_fst + (sp.as_nat(match_pair_minter_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_273_snd), (match_pair_minter_271_fst, (sp.as_nat(match_pair_minter_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))))))) >= self.data.collateralizationPercentage, 11)
    self.data.interestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))
    self.data.lastInterestIndexUpdateTime = sp.add_seconds(self.data.lastInterestIndexUpdateTime, sp.to_int((sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60) * 60))
    sp.set_type(match_pair_minter_268_fst, sp.TAddress)
    sp.set_type(match_pair_minter_271_fst, sp.TNat)
    sp.set_type(sp.as_nat(match_pair_minter_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_273_snd), (match_pair_minter_271_fst, (sp.as_nat(match_pair_minter_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))))))), sp.TNat)
    sp.set_type(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60))), sp.TNat)
    sp.set_type(match_pair_minter_272_fst, sp.TBool)
    sp.set_type(sp.mul(match_pair_minter_270_fst // 1000000000000, sp.mutez(1)) - sp.snd(match_pair_minter_273_snd), sp.TMutez)
    sp.transfer((match_pair_minter_268_fst, (match_pair_minter_271_fst, (sp.to_int(sp.as_nat(match_pair_minter_273_fst) + self.calculateNewAccruedInterest((sp.fst(match_pair_minter_273_snd), (match_pair_minter_271_fst, (sp.as_nat(match_pair_minter_273_fst), self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))))))), (sp.to_int(self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime) // 60)))), match_pair_minter_272_fst)))), sp.mul(match_pair_minter_270_fst // 1000000000000, sp.mutez(1)) - sp.snd(match_pair_minter_273_snd), sp.contract(sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))), self.data.ovenProxyContractAddress, entry_point='updateState').open_some())
    sp.send(match_pair_minter_269_fst, sp.snd(match_pair_minter_273_snd))

  @sp.global_lambda
  def calculateNewAccruedInterest(_x0):
    sp.set_type(_x0, sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))
    sp.result(sp.as_nat(sp.fst(sp.ediv(sp.fst(sp.ediv(sp.snd(sp.snd(sp.snd(_x0))) * 1000000000000000000, sp.as_nat(sp.fst(_x0))).open_some()) * (sp.fst(sp.snd(_x0)) + sp.fst(sp.snd(sp.snd(_x0)))), 1000000000000000000).open_some()) - (sp.fst(sp.snd(_x0)) + sp.fst(sp.snd(sp.snd(_x0))))))

  @sp.global_lambda
  def compoundWithLinearApproximation(_x1):
    sp.set_type(_x1, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))
    sp.result((sp.fst(_x1) * (1000000000000000000 + (sp.snd(sp.snd(_x1)) * sp.fst(sp.snd(_x1))))) // 1000000000000000000)

  @sp.global_lambda
  def computeCollateralizationPercentage(_x2):
    sp.set_type(_x2, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))
    sp.result(((((sp.fst(_x2) * sp.fst(sp.snd(_x2))) // 1000000000000000000) * 1000000000000000000) // sp.snd(sp.snd(_x2))) * 100)

sp.add_compilation_target("test", Contract())