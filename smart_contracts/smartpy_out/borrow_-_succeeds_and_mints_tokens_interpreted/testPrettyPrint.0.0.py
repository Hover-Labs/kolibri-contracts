import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(borrow_borrowedTokens = 0, borrow_liquidated = False, borrow_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), borrow_ovenBalance = 0, borrow_ovenInterestIndex = 0, borrow_ownerAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), borrow_stabilityFeeTokens = 0, borrow_tokensToBorrow = 0, deposit_borrowedTokens = 0, deposit_liquidated = False, deposit_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), deposit_ovenBalance = 0, deposit_ovenInterestIndex = 0, deposit_ownerAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), deposit_stabilityFeeTokens = 0, liquidate_borrowedTokens = 0, liquidate_liquidated = False, liquidate_liquidatorAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), liquidate_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), liquidate_ovenBalance = 0, liquidate_ovenInterestIndex = 0, liquidate_ownerAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), liquidate_stabilityFeeTokens = 0, repay_borrowedTokens = 0, repay_liquidated = False, repay_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), repay_ovenBalance = 0, repay_ovenInterestIndex = 0, repay_ownerAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), repay_stabilityFeeTokens = 0, repay_tokensToRepay = 0, updateState_borrowedTokens = 0, updateState_interestIndex = 0, updateState_isLiquidated = False, updateState_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), updateState_stabilityFeeTokens = 0, withdraw_borrowedTokens = 0, withdraw_liquidated = False, withdraw_mutezToWithdraw = sp.tez(0), withdraw_ovenAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), withdraw_ovenBalance = 0, withdraw_ovenInterestIndex = 0, withdraw_ownerAddress = sp.address('tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA'), withdraw_stabilityFeeTokens = 0)

  @sp.entry_point
  def borrow(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    self.data.borrow_ovenAddress = sp.fst(params)
    self.data.borrow_ownerAddress = sp.fst(sp.snd(params))
    self.data.borrow_ovenBalance = sp.fst(sp.snd(sp.snd(params)))
    self.data.borrow_borrowedTokens = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.borrow_liquidated = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(params)))))
    self.data.borrow_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))
    self.data.borrow_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))
    self.data.borrow_tokensToBorrow = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))

  @sp.entry_point
  def deposit(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TInt)))))))
    self.data.deposit_ovenAddress = sp.fst(params)
    self.data.deposit_ownerAddress = sp.fst(sp.snd(params))
    self.data.deposit_ovenBalance = sp.fst(sp.snd(sp.snd(params)))
    self.data.deposit_borrowedTokens = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.deposit_liquidated = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(params)))))
    self.data.deposit_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))
    self.data.deposit_ovenInterestIndex = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TAddress))))))))
    self.data.liquidate_ovenAddress = sp.fst(params)
    self.data.liquidate_ownerAddress = sp.fst(sp.snd(params))
    self.data.liquidate_ovenBalance = sp.fst(sp.snd(sp.snd(params)))
    self.data.liquidate_borrowedTokens = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.liquidate_liquidated = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(params)))))
    self.data.liquidate_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))
    self.data.liquidate_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))
    self.data.liquidate_liquidatorAddress = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))

  @sp.entry_point
  def repay(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TNat))))))))
    self.data.repay_ovenAddress = sp.fst(params)
    self.data.repay_ownerAddress = sp.fst(sp.snd(params))
    self.data.repay_ovenBalance = sp.fst(sp.snd(sp.snd(params)))
    self.data.repay_borrowedTokens = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.repay_liquidated = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(params)))))
    self.data.repay_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))
    self.data.repay_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))
    self.data.repay_tokensToRepay = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))

  @sp.entry_point
  def updateState(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TBool)))))
    self.data.updateState_ovenAddress = sp.fst(params)
    self.data.updateState_borrowedTokens = sp.fst(sp.snd(params))
    self.data.updateState_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(params)))
    self.data.updateState_interestIndex = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.updateState_isLiquidated = sp.snd(sp.snd(sp.snd(sp.snd(params))))

  @sp.entry_point
  def withdraw(self, params):
    sp.set_type(params, sp.TPair(sp.TAddress, sp.TPair(sp.TAddress, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TPair(sp.TBool, sp.TPair(sp.TInt, sp.TPair(sp.TInt, sp.TMutez))))))))
    self.data.withdraw_ovenAddress = sp.fst(params)
    self.data.withdraw_ownerAddress = sp.fst(sp.snd(params))
    self.data.withdraw_ovenBalance = sp.fst(sp.snd(sp.snd(params)))
    self.data.withdraw_borrowedTokens = sp.fst(sp.snd(sp.snd(sp.snd(params))))
    self.data.withdraw_liquidated = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(params)))))
    self.data.withdraw_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params))))))
    self.data.withdraw_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))
    self.data.withdraw_mutezToWithdraw = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(params)))))))