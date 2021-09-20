# Partial mock of the OvenProxy contract and captures values for inspection.

import smartpy as sp

Addresses = sp.import_script_from_url("file:./test-helpers/addresses.py")
OvenApi = sp.import_script_from_url("file:./common/oven-api.py")

class MockOvenProxyContract(sp.Contract):
    def __init__(
        self,
    ):
      self.init(
        # borrow parameters.
        borrow_ovenAddress = Addresses.NULL_ADDRESS,
        borrow_ownerAddress = Addresses.NULL_ADDRESS,
        borrow_ovenBalance = sp.nat(0),
        borrow_borrowedTokens = sp.nat(0),
        borrow_liquidated = sp.bool(False),
        borrow_stabilityFeeTokens = sp.int(0),
        borrow_ovenInterestIndex = sp.int(0),
        borrow_tokensToBorrow = sp.nat(0),

        # repay parameters.
        repay_ovenAddress = Addresses.NULL_ADDRESS,
        repay_ownerAddress = Addresses.NULL_ADDRESS,
        repay_ovenBalance = sp.nat(0),
        repay_borrowedTokens = sp.nat(0),
        repay_liquidated = sp.bool(False),
        repay_stabilityFeeTokens = sp.int(0),
        repay_ovenInterestIndex = sp.int(0),
        repay_tokensToRepay = sp.nat(0),

        # deposit parameters
        deposit_ovenAddress = Addresses.NULL_ADDRESS,
        deposit_ownerAddress = Addresses.NULL_ADDRESS,
        deposit_ovenBalance = sp.nat(0),
        deposit_borrowedTokens = sp.nat(0),
        deposit_liquidated = sp.bool(False),
        deposit_stabilityFeeTokens = sp.int(0),
        deposit_ovenInterestIndex = sp.int(0),

        # withdraw parameters
        withdraw_ovenAddress = Addresses.NULL_ADDRESS,
        withdraw_ownerAddress = Addresses.NULL_ADDRESS,
        withdraw_ovenBalance = sp.nat(0),
        withdraw_borrowedTokens = sp.nat(0),
        withdraw_liquidated = sp.bool(False),
        withdraw_stabilityFeeTokens = sp.int(0),
        withdraw_ovenInterestIndex = sp.int(0),
        withdraw_mutezToWithdraw = sp.mutez(0),

        # liquidate parameters
        liquidate_ovenAddress = Addresses.NULL_ADDRESS,
        liquidate_ownerAddress = Addresses.NULL_ADDRESS,
        liquidate_ovenBalance = sp.nat(0),
        liquidate_borrowedTokens = sp.nat(0),
        liquidate_liquidated = sp.bool(False),
        liquidate_stabilityFeeTokens = sp.int(0),
        liquidate_ovenInterestIndex = sp.int(0),
        liquidate_liquidatorAddress = Addresses.NULL_ADDRESS,

        # updateState parameters
        updateState_ovenAddress = Addresses.NULL_ADDRESS,
        updateState_borrowedTokens = sp.nat(0),
        updateState_stabilityFeeTokens = sp.int(0),
        updateState_interestIndex = sp.int(0),
        updateState_isLiquidated = False
      )

    ################################################################
    # Oven Interface
    ################################################################

    @sp.entry_point
    def borrow(self, param):
        sp.set_type(param, OvenApi.BORROW_PARAMETER_TYPE)

        self.data.borrow_ovenAddress        = sp.fst(param) 
        self.data.borrow_ownerAddress       = sp.fst(sp.snd(param))
        self.data.borrow_ovenBalance        = sp.fst(sp.snd(sp.snd(param)))
        self.data.borrow_borrowedTokens     = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.borrow_liquidated         = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(param)))))
        self.data.borrow_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))
        self.data.borrow_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))
        self.data.borrow_tokensToBorrow     = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))

    @sp.entry_point
    def repay(self, param):
        sp.set_type(param, OvenApi.REPAY_PARAMETER_TYPE)

        self.data.repay_ovenAddress         = sp.fst(param) 
        self.data.repay_ownerAddress        = sp.fst(sp.snd(param))
        self.data.repay_ovenBalance         = sp.fst(sp.snd(sp.snd(param)))
        self.data.repay_borrowedTokens      = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.repay_liquidated          = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(param)))))
        self.data.repay_stabilityFeeTokens  = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))
        self.data.repay_ovenInterestIndex  = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))
        self.data.repay_tokensToRepay       = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))        

    @sp.entry_point
    def deposit(self, param):
        sp.set_type(param, OvenApi.DEPOSIT_PARAMETER_TYPE)

        self.data.deposit_ovenAddress         = sp.fst(param) 
        self.data.deposit_ownerAddress        = sp.fst(sp.snd(param))
        self.data.deposit_ovenBalance         = sp.fst(sp.snd(sp.snd(param)))
        self.data.deposit_borrowedTokens      = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.deposit_liquidated          = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(param)))))
        self.data.deposit_stabilityFeeTokens  = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))
        self.data.deposit_ovenInterestIndex  = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))

    @sp.entry_point
    def withdraw(self, param):
        sp.set_type(param, OvenApi.WITHDRAW_PARAMETER_TYPE)

        self.data.withdraw_ovenAddress         = sp.fst(param) 
        self.data.withdraw_ownerAddress        = sp.fst(sp.snd(param))
        self.data.withdraw_ovenBalance         = sp.fst(sp.snd(sp.snd(param)))
        self.data.withdraw_borrowedTokens      = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.withdraw_liquidated          = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(param)))))
        self.data.withdraw_stabilityFeeTokens  = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))
        self.data.withdraw_ovenInterestIndex  = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))
        self.data.withdraw_mutezToWithdraw     = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))        

    @sp.entry_point
    def liquidate(self, param):
        sp.set_type(param, OvenApi.LIQUIDATE_PARAMETER_TYPE)

        self.data.liquidate_ovenAddress        = sp.fst(param) 
        self.data.liquidate_ownerAddress       = sp.fst(sp.snd(param))
        self.data.liquidate_ovenBalance        = sp.fst(sp.snd(sp.snd(param)))
        self.data.liquidate_borrowedTokens     = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.liquidate_liquidated         = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(param)))))
        self.data.liquidate_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param))))))
        self.data.liquidate_ovenInterestIndex = sp.fst(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))
        self.data.liquidate_liquidatorAddress = sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(sp.snd(param)))))))

    @sp.entry_point
    def updateState(self, param):
        sp.set_type(param, OvenApi.UPDATE_STATE_PARAMETER_TYPE)

        self.data.updateState_ovenAddress        = sp.fst(param)
        self.data.updateState_borrowedTokens     = sp.fst(sp.snd(param))
        self.data.updateState_stabilityFeeTokens = sp.fst(sp.snd(sp.snd(param)))
        self.data.updateState_interestIndex      = sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.updateState_isLiquidated       = sp.snd(sp.snd(sp.snd(sp.snd(param))))