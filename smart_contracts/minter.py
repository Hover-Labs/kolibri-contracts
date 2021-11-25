import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")
OvenApi = sp.io.import_script_from_url("file:common/oven-api.py")

################################################################
# Contract
################################################################

class MinterContract(sp.Contract):
    def __init__(
        self,
        tokenContractAddress = Addresses.TOKEN_ADDRESS,
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,  
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS,
        stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
        liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS,
        collateralizationPercentage = sp.nat(200000000000000000000), # 200%
        privateOwnerLiquidationThreshold = sp.nat(20000000000000000000), # 20%
        stabilityFee = sp.nat(0),
        lastInterestIndexUpdateTime = sp.timestamp(1601871456),
        interestIndex = 1000000000000000000,
        # The amount of interest given to the dev fund.
        # Implicitly (1 - <dev fund split>) is given to the stability fund.
        devFundSplit = sp.nat(100000000000000000), # 10%
        liquidationFeePercent = sp.nat(80000000000000000),  # 8%
        amountLoaned = sp.nat(0),

        # Initialization for KIP-009
        # See: https://discuss.kolibri.finance/t/kip-009-interest-at-accrual-time-rather-than-repayment-time/78/2
        # NOTE: In a production deploy, `initialized` should be set to False. We set it to True here to make it easy for
        #       existing tests to continue passing
        initialized = True,
        initializerContractAddress = Addresses.INITIALIZER_ADDRESS,
    ):
        self.exception_optimization_level = "DefaultUnit"
        self.add_flag("erase-comments")

        self.init(
            # Contract Addresses
            governorContractAddress = governorContractAddress,
            tokenContractAddress = tokenContractAddress,
            ovenProxyContractAddress = ovenProxyContractAddress,
            collateralizationPercentage = collateralizationPercentage,
            developerFundContractAddress = developerFundContractAddress,
            stabilityFundContractAddress = stabilityFundContractAddress,
            liquidityPoolContractAddress = liquidityPoolContractAddress,

            # Configuration Parameters
            liquidationFeePercent = liquidationFeePercent,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            devFundSplit = devFundSplit,
 
            # Interest Calculations
            amountLoaned = amountLoaned,
            interestIndex = interestIndex,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = lastInterestIndexUpdateTime,

            # Initialization for KIP-009
            # See: https://discuss.kolibri.finance/t/kip-009-interest-at-accrual-time-rather-than-repayment-time/78/2
            initialized = initialized,
            initializerContractAddress = initializerContractAddress,
        )

        self.compoundWithLinearApproximation = sp.private_lambda(
            name="compoundWithLinearApproximation", 
            with_storage="read-only"
        )(MinterContract.compoundWithLinearApproximation_implementation)


    ################################################################
    # KIP-009
    ################################################################
      
    # Initialize the global accumulator
    @sp.entry_point
    def initialize(self, amountLoaned):
        # Verify contract is not already initialized.
        sp.verify(self.data.initialized == False, Errors.ALREADY_INITIALIZED)

        # Verify sender can initialize the contract.
        sp.verify(sp.sender == self.data.initializerContractAddress, Errors.BAD_SENDER)

        # Set up global interest accumulator.
        self.data.amountLoaned = amountLoaned

        # Set contract to be initialized
        self.data.initialized = True

    ################################################################
    # Views
    ################################################################

    # # Get oven's total balance, given the oven's data.
    # #
    # # Parameter:
    # # - ovenBorrowedTokens: The number of tokens loaned against an oven.
    # # - ovenStabilityFeeTokens: The number of tokens the oven has accrued in stability fees.
    # # - ovenInterestIndex: The interest index of the oven.
    # @sp.onchain_view()
    # def getOvenLoanAmount(self, param):
    #     sp.set_type(
    #         param, 
    #         sp.TRecord(
    #             ovenBorrowedTokens = sp.TNat,
    #             ovenStabilityFeeTokens = sp.TInt,
    #             ovenInterestIndex = sp.TInt,
    #         )            
    #     )

    #     # Compound interest
    #     timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
    #     numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
    #     newMinterInterestIndex = self.compoundWithLinearApproximation(
    #         (
    #             self.data.interestIndex, 
    #             (
    #                 self.data.stabilityFee, 
    #                 numPeriods
    #             )
    #         )
    #     )

    #     # Calculate newly accrued interest
    #     newInterest = self.calculateNewAccruedInterest(
    #         (
    #             (
    #                 param.ovenInterestIndex,
    #                 (
    #                     (
    #                         param.ovenBorrowedTokens,
    #                         (
    #                             sp.as_nat(param.ovenStabilityFeeTokens),
    #                             newMinterInterestIndex
    #                         )
    #                     )
    #                 )
    #             )
    #         )
    #     )

    #     # Return oven borrowed tokens + oven stability fees + new interest
    #     sp.result(param.ovenBorrowedTokens + sp.as_nat(param.ovenStabilityFeeTokens) + newInterest)

    # Get the current stability fee.
    @sp.onchain_view()
    def getStabilityFee(self):
        sp.result(self.data.stabilityFee)

    # Get the current interest index.
    @sp.onchain_view()
    def getCurrentInterestIndex(self):
        compoundWithLinearApproximationInlined = sp.build_lambda(self.compoundWithLinearApproximation_implementation)

        # Compound interest
        # TODO(keefertaylor): This code is duplicated here, in getAmountLoaned and probably elsewhere. Attempt to dedupe.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = compoundWithLinearApproximationInlined((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        sp.result(newMinterInterestIndex)

    # # Get the current amount loaned
    # @sp.onchain_view()
    # def getAmountLoaned(self):
    #     # Compound interest
    #     timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
    #     numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
    #     newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

    #     newAmountLoaned = sp.local(
    #         'newAmountLoaned', 
    #         self.compoundWithLinearApproximation(
    #             (
    #                 self.data.amountLoaned,
    #                 (
    #                     self.data.stabilityFee, 
    #                     numPeriods
    #                 )
    #             )
    #         )
    #     )

    #     sp.result(newAmountLoaned.value)

    # Get the totality of the Minter storage, to parse in the client.
    @sp.onchain_view()
    def getStorage(self):
        sp.result(self.data)

    ################################################################
    # Public Interface
    ################################################################

    # Get interest index
    # DEPRECATED: This method will be removed in a future release. Please use the `getInterestIndex` on chain view
    #             instead.
    @sp.entry_point
    def getInterestIndex(self, param):        
        sp.set_type(param, sp.TContract(sp.TNat))

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Compound interest
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Transfer results to requester.
        sp.transfer(newMinterInterestIndex, sp.mutez(0), param)

        # Accrue interest on the global accumulator and mint to developer and stability fund and update the global accumulator
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))
        self.data.amountLoaned = newAmountLoaned.value

        # Update internal state.
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    ################################################################
    # Oven Interface
    ################################################################

    # borrow
    @sp.entry_point
    def borrow(self, param):
        sp.set_type(param, OvenApi.BORROW_PARAMETER_TYPE_ORACLE)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the sender is the oven proxy.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)

        # Destructure input params.        
        oraclePrice,           pair1 = sp.match_pair(param)
        ovenAddress,           pair2 = sp.match_pair(pair1)
        ownerAddress,          pair3 = sp.match_pair(pair2)
        ovenBalance,           pair4 = sp.match_pair(pair3)
        borrowedTokens,        pair5 = sp.match_pair(pair4)
        isLiquidated,          pair6 = sp.match_pair(pair5)
        stabilityFeeTokensInt, pair7 = sp.match_pair(pair6)
        interestIndex                = sp.fst(pair7)
        tokensToBorrow               = sp.snd(pair7)

        stabilityFeeTokens = sp.as_nat(stabilityFeeTokensInt)

        sp.set_type(oraclePrice, sp.TNat)
        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(ownerAddress, sp.TAddress)
        sp.set_type(ovenBalance, sp.TNat)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TInt)
        sp.set_type(tokensToBorrow, sp.TNat)

        # Calculate new interest indices for the minter and the oven.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Disallow repay operations on liquidated ovens.
        sp.verify(isLiquidated == False, message = Errors.LIQUIDATED)

        # Calculate newly accrued stability fees and determine total fees.
        accruedStabilityFeeTokens = self.calculateNewAccruedInterest((interestIndex, (borrowedTokens, (stabilityFeeTokens, (newMinterInterestIndex)))))
        newStabilityFeeTokens = stabilityFeeTokens + accruedStabilityFeeTokens

        # Compute new borrowed amount.
        newTotalBorrowedTokens = borrowedTokens + tokensToBorrow
        sp.set_type(newTotalBorrowedTokens, sp.TNat)

        # Verify the oven is not under-collateralized. 
        totalOutstandingTokens = sp.local('totalOutstandingTokens', newTotalBorrowedTokens + newStabilityFeeTokens)
        sp.if totalOutstandingTokens.value > 0:
            newCollateralizationPercentage = self.computeCollateralizationPercentage((ovenBalance, (oraclePrice, totalOutstandingTokens.value)))
            sp.verify(newCollateralizationPercentage >= self.data.collateralizationPercentage, message = Errors.OVEN_UNDER_COLLATERALIZED)

        # Call mint in token contract
        self.mintTokens(tokensToBorrow, ownerAddress)

        # Inform oven of new state.
        self.updateOvenState(ovenAddress, newTotalBorrowedTokens, newStabilityFeeTokens, newMinterInterestIndex, isLiquidated, sp.balance)

        # Accrue interest on the global accumulator and mint to developer and stability fund.
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))

        # Update the total amountLoaned 
        # New total loaned = value of amountLoaned after accruing interest until now + newly borrowed tokens
        self.data.amountLoaned = newAmountLoaned.value + tokensToBorrow

        # Update internal state
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    # repay
    @sp.entry_point
    def repay(self, param):
        sp.set_type(param, OvenApi.REPAY_PARAMETER_TYPE)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the sender is the oven proxy.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)

        # Destructure input params.        
        ovenAddress,           pair1 = sp.match_pair(param)
        ownerAddress,          pair2 = sp.match_pair(pair1)
        ovenBalance,           pair3 = sp.match_pair(pair2)
        borrowedTokens,        pair4 = sp.match_pair(pair3)
        isLiquidated,          pair5 = sp.match_pair(pair4)
        stabilityFeeTokensInt, pair6 = sp.match_pair(pair5)
        interestIndex                = sp.fst(pair6)
        tokensToRepay                = sp.snd(pair6)

        stabilityFeeTokens = sp.as_nat(stabilityFeeTokensInt)

        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(ownerAddress, sp.TAddress)
        sp.set_type(ovenBalance, sp.TNat)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TInt)
        sp.set_type(tokensToRepay, sp.TNat)

        # Calculate new interest indices for the minter and the oven.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Disallow repay operations on liquidated ovens.
        sp.verify(isLiquidated == False, message = Errors.LIQUIDATED)

        # Calculate newly accrued stability fees and determine total fees.
        accruedStabilityFeeTokens = self.calculateNewAccruedInterest((interestIndex, (borrowedTokens, (stabilityFeeTokens, (newMinterInterestIndex)))))
        newStabilityFeeTokens = stabilityFeeTokens + accruedStabilityFeeTokens

        # Verify the user is not trying to repay more tokens than they owe.
        totalOwedFromOven = newStabilityFeeTokens + borrowedTokens
        sp.verify(tokensToRepay <= totalOwedFromOven, Errors.REPAID_MORE_THAN_OWED)

        # Determine new values for stability fee tokens and borrowed token value. 
        # Also, note down the number of stability fee tokens repaid.
        stabilityFeeTokensRepaid = sp.local("stabilityFeeTokensRepaid", 0)
        remainingStabilityFeeTokens = sp.local("remainingStabilityFeeTokens", 0)
        remainingBorrowedTokenBalance = sp.local("remainingBorrowedTokenBalance", 0)
        sp.if tokensToRepay < newStabilityFeeTokens:
            stabilityFeeTokensRepaid.value = tokensToRepay
            remainingStabilityFeeTokens.value = sp.as_nat(newStabilityFeeTokens - tokensToRepay)
            remainingBorrowedTokenBalance.value = borrowedTokens
        sp.else:
            stabilityFeeTokensRepaid.value = newStabilityFeeTokens
            remainingStabilityFeeTokens.value = sp.nat(0)
            remainingBorrowedTokenBalance.value = sp.as_nat(borrowedTokens - sp.as_nat(tokensToRepay - newStabilityFeeTokens))

        # Burn the tokens repaid.
        self.burnTokens(tokensToRepay, ownerAddress)

        # Accrue interest on the global accumulator and mint to developer and stability fund.
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))

        # Update the total amountLoaned 
        # New total loaned = value of amountLoaned after accruing interest until now - newly repaid tokens
        self.data.amountLoaned = sp.as_nat(newAmountLoaned.value - tokensToRepay)

        # Inform oven of new state.
        self.updateOvenState(ovenAddress, remainingBorrowedTokenBalance.value, remainingStabilityFeeTokens.value, newMinterInterestIndex, isLiquidated, sp.balance)

        # Update internal state
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    # deposit
    @sp.entry_point
    def deposit(self, param):
        sp.set_type(param, OvenApi.DEPOSIT_PARAMETER_TYPE)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the sender is a oven.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)

        # Destructure input params.        
        ovenAddress,           pair1 = sp.match_pair(param)
        ownerAddress,          pair2 = sp.match_pair(pair1)
        ovenBalance,           pair3 = sp.match_pair(pair2)
        borrowedTokens,        pair4 = sp.match_pair(pair3)
        isLiquidated,          pair5 = sp.match_pair(pair4)
        stabilityFeeTokensInt        = sp.fst(pair5)
        interestIndex                = sp.snd(pair5)

        stabilityFeeTokens = sp.as_nat(stabilityFeeTokensInt)

        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(ownerAddress, sp.TAddress)
        sp.set_type(ovenBalance, sp.TNat)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TInt)

        # Calculate new interest indices for the minter and the oven.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Disallow deposit operations on liquidated ovens.
        sp.verify(isLiquidated == False, message = Errors.LIQUIDATED)

        # Calculate newly accrued stability fees and determine total fees.
        accruedStabilityFeeTokens = self.calculateNewAccruedInterest((interestIndex, (borrowedTokens, (stabilityFeeTokens, (newMinterInterestIndex)))))
        newStabilityFeeTokens = stabilityFeeTokens + accruedStabilityFeeTokens

        # Intentional no-op. Pass value back to oven.
        self.updateOvenState(ovenAddress, borrowedTokens, newStabilityFeeTokens, newMinterInterestIndex, isLiquidated, sp.balance)

        # Update the global accumulator and mint new tokens
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))
        self.data.amountLoaned = newAmountLoaned.value

        # Update internal state
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    @sp.entry_point
    def withdraw(self, param):
        sp.set_type(param, OvenApi.WITHDRAW_PARAMETER_TYPE_ORACLE)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the sender is a oven.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)

        # Destructure input params.        
        oraclePrice,           pair1 = sp.match_pair(param)
        ovenAddress,           pair2 = sp.match_pair(pair1)
        ownerAddress,          pair3 = sp.match_pair(pair2)
        ovenBalance,           pair4 = sp.match_pair(pair3)
        borrowedTokens,        pair5 = sp.match_pair(pair4)
        isLiquidated,          pair6 = sp.match_pair(pair5)
        stabilityFeeTokensInt, pair7 = sp.match_pair(pair6)
        interestIndex                = sp.fst(pair7)
        mutezToWithdraw              = sp.snd(pair7)

        stabilityFeeTokens = sp.as_nat(stabilityFeeTokensInt)

        sp.set_type(oraclePrice, sp.TNat)
        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(ownerAddress, sp.TAddress)
        sp.set_type(ovenBalance, sp.TNat)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TInt)
        sp.set_type(mutezToWithdraw, sp.TMutez)

        # Calculate new interest indices for the minter and the oven.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Calculate newly accrued stability fees and determine total fees.
        accruedStabilityFeeTokens = self.calculateNewAccruedInterest((interestIndex, (borrowedTokens, (stabilityFeeTokens, (newMinterInterestIndex)))))
        newStabilityFeeTokens = stabilityFeeTokens + accruedStabilityFeeTokens

        # Verify the oven has not become under-collateralized.
        totalOutstandingTokens = borrowedTokens + newStabilityFeeTokens
        sp.if totalOutstandingTokens > 0:
            withdrawAmount = sp.fst(sp.ediv(mutezToWithdraw, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
            newOvenBalance = sp.as_nat(ovenBalance - withdrawAmount)
            newCollateralizationPercentage = self.computeCollateralizationPercentage((newOvenBalance, (oraclePrice, totalOutstandingTokens))) 
            sp.verify(newCollateralizationPercentage >= self.data.collateralizationPercentage, message = Errors.OVEN_UNDER_COLLATERALIZED)

        # Withdraw mutez to the owner.
        sp.send(ownerAddress, mutezToWithdraw)

        # Update the oven's state and return the remaining mutez to it.
        remainingMutez = sp.utils.nat_to_mutez(ovenBalance // Constants.MUTEZ_TO_KOLIBRI_CONVERSION) - mutezToWithdraw
        self.updateOvenState(ovenAddress, borrowedTokens, newStabilityFeeTokens, newMinterInterestIndex, isLiquidated, remainingMutez)
        
        # Update the global accumulator and mint new tokens
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))
        self.data.amountLoaned = newAmountLoaned.value

        # Update internal state
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    # liquidate
    @sp.entry_point
    def liquidate(self, param):
        sp.set_type(param, OvenApi.LIQUIDATE_PARAMETER_TYPE_ORACLE)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Verify the sender is a oven.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)

        # Destructure input params.        
        oraclePrice,           pair1 = sp.match_pair(param)
        ovenAddress,           pair2 = sp.match_pair(pair1)
        ownerAddress,          pair3 = sp.match_pair(pair2)
        ovenBalance,           pair4 = sp.match_pair(pair3)
        borrowedTokens,        pair5 = sp.match_pair(pair4)
        isLiquidated,          pair6 = sp.match_pair(pair5)
        stabilityFeeTokensInt, pair7 = sp.match_pair(pair6)
        interestIndex                = sp.fst(pair7)
        liquidatorAddress            = sp.snd(pair7)

        stabilityFeeTokens = sp.as_nat(stabilityFeeTokensInt)

        sp.set_type(oraclePrice, sp.TNat)
        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(ownerAddress, sp.TAddress)
        sp.set_type(ovenBalance, sp.TNat)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TInt)
        sp.set_type(liquidatorAddress, sp.TAddress)

        # Calculate new interest indices for the minter and the oven.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods)))

        # Disallow additional liquidate operations on liquidated ovens.
        sp.verify(isLiquidated == False, message = Errors.LIQUIDATED)

        # Calculate newly accrued stability fees and determine total fees.
        accruedStabilityFeeTokens = self.calculateNewAccruedInterest((interestIndex, (borrowedTokens, (stabilityFeeTokens, (newMinterInterestIndex)))))
        newStabilityFeeTokens = stabilityFeeTokens + accruedStabilityFeeTokens

        # Verify oven is under collateralized
        totalOutstandingTokens = borrowedTokens + newStabilityFeeTokens
        collateralizationPercentage = self.computeCollateralizationPercentage((ovenBalance, (oraclePrice, totalOutstandingTokens)))
        sp.verify(collateralizationPercentage < self.data.collateralizationPercentage, message = Errors.NOT_UNDER_COLLATERALIZED)

        # Verify liquidation is allowed.
        # Undercollateralization is performed as a check above.
        # Liquidity Pool and Stability Fund can always liquidate, others must be below privateLiquidationFeePercentage
        privateLiquidationRequirement = sp.as_nat(self.data.collateralizationPercentage - self.data.privateOwnerLiquidationThreshold)
        sp.verify(
            (liquidatorAddress == self.data.liquidityPoolContractAddress) | # sender is liquidity pool
            (liquidatorAddress == self.data.stabilityFundContractAddress) | # sender is stability fund
            (collateralizationPercentage < privateLiquidationRequirement), # sender is private and collateralization is below privateLiquidationFeePercentage
            Errors.NOT_ALLOWED_TO_LIQUIDATE
        )

        # Calculate a liquidation fee.
        liquidationFee = (totalOutstandingTokens * self.data.liquidationFeePercent) // Constants.PRECISION

        # Burn tokens from the liquidator to pay for the Oven.
        self.burnTokens((totalOutstandingTokens + liquidationFee), liquidatorAddress)
                
        # Send collateral to liquidator.
        sp.send(liquidatorAddress, sp.utils.nat_to_mutez(ovenBalance // Constants.MUTEZ_TO_KOLIBRI_CONVERSION))

        # Inform oven it is liquidated, clear owed tokens and return no collateral.
        self.updateOvenState(ovenAddress, sp.nat(0), sp.nat(0), newMinterInterestIndex, True, sp.mutez(0))

        # Accrue interest on the global accumulator
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods
                    )
                )
            )
        )

        # Mint tokens to the developer and stability funds. 
        # Amount to mint = new interest accrued globally + liquidation fee
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned) + liquidationFee)

        # Update the total amountLoaned 
        # New total loaned = value of amountLoaned after accruing interest until now - tokens repaid to liquidate oven
        self.data.amountLoaned = sp.as_nat(newAmountLoaned.value - totalOutstandingTokens)
        
        # Update internal state
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods * Constants.SECONDS_PER_COMPOUND))

    ################################################################
    # Governance
    #
    # Some of these are lumped together to avoid excessive contract
    # size.
    ################################################################

    @sp.entry_point
    def setStabilityFee(self, newStabilityFee):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        # Verify the contract is initialized.
        sp.verify(self.data.initialized == True, message = Errors.NOT_INITIALIZED)

        # Compound interest and update internal state.
        timeDeltaSeconds = sp.as_nat(sp.now - self.data.lastInterestIndexUpdateTime)
        numPeriods = sp.local('numPeriods', timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND)
        newMinterInterestIndex = self.compoundWithLinearApproximation((self.data.interestIndex, (self.data.stabilityFee, numPeriods.value)))
        self.data.interestIndex = newMinterInterestIndex
        self.data.lastInterestIndexUpdateTime = self.data.lastInterestIndexUpdateTime.add_seconds(sp.to_int(numPeriods.value * Constants.SECONDS_PER_COMPOUND))

        # Update the global accumulator and mint new tokens
        newAmountLoaned = sp.local(
            'newAmountLoaned', 
            self.compoundWithLinearApproximation(
                (
                    self.data.amountLoaned,
                    (
                        self.data.stabilityFee, 
                        numPeriods.value
                    )
                )
            )
        )
        self.mintTokensToStabilityAndDevFund(sp.as_nat(newAmountLoaned.value - self.data.amountLoaned))
        self.data.amountLoaned = newAmountLoaned.value

        self.data.stabilityFee = newStabilityFee

    @sp.entry_point
    def setLiquidationFeePercent(self, newLiquidationFeePercent):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.liquidationFeePercent = newLiquidationFeePercent

    @sp.entry_point
    def setCollateralizationPercentage(self, newCollateralizationPercentage):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.collateralizationPercentage = newCollateralizationPercentage

    @sp.entry_point
    def setLiquidityPoolContract(self, newLiquidityPoolContract):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.liquidityPoolContractAddress = newLiquidityPoolContract

    @sp.entry_point
    def setPrivateLiquidationThreshold(self, newValue):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.privateOwnerLiquidationThreshold = newValue

    @sp.entry_point   
    def setGovernorContract(self, newGovernorContract):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContract

    @sp.entry_point
    def setTokenContract(self, newTokenContract):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.tokenContractAddress = newTokenContract

    @sp.entry_point
    def setOvenProxyContract(self, newOvenProxyContract):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenProxyContractAddress = newOvenProxyContract       

    @sp.entry_point
    def setStabilityFundContract(self, newStabilityFund):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.stabilityFundContractAddress = newStabilityFund
        
    @sp.entry_point
    def setDeveloperFundContract(self, newDeveloperFund):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.developerFundContractAddress = newDeveloperFund      

    @sp.entry_point
    def setInitializerContract(self, newInitializer):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.initializerContractAddress = newInitializer      

    # Update the splits between the funds
    @sp.entry_point
    def updateFundSplits(self, newSplits):
        sp.set_type(newSplits, sp.TRecord(
            developerFundSplit = sp.TNat,
            stabilityFundSplit = sp.TNat,
        ).layout(("developerFundSplit", "stabilityFundSplit")))

        # Verify splits sum to 1.0
        sp.verify((newSplits.developerFundSplit + newSplits.stabilityFundSplit) == Constants.PRECISION, Errors.BAD_SPLITS)

        # Verify sender is the governor
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        self.data.devFundSplit = newSplits.developerFundSplit
     
    ################################################################
    # Helpers
    ################################################################

    # Mint tokens to a stability fund.
    # 
    # This function does *NOT* burn tokens - the caller must do this. This is an efficiency gain because normally
    # we would burn tokens for collateral + stability fees.
    def mintTokensToStabilityAndDevFund(self, tokensToMint):
        sp.set_type(tokensToMint, sp.TNat)

        # Determine proportion of tokens minted to dev fund.
        tokensForDevFund = (tokensToMint * self.data.devFundSplit) // Constants.PRECISION
        tokensForStabilityFund = sp.as_nat(tokensToMint - tokensForDevFund)

        # Mint tokens
        self.mintTokens(tokensForDevFund, self.data.developerFundContractAddress)
        self.mintTokens(tokensForStabilityFund, self.data.stabilityFundContractAddress)

    def burnTokens(self, tokensToBurn, address):
        sp.set_type(tokensToBurn, sp.TNat)
        sp.set_type(address, sp.TAddress)

        tokenContractParam = sp.record(address= address, value= tokensToBurn)
        contractHandle = sp.contract(
            sp.TRecord(address = sp.TAddress, value = sp.TNat),
            self.data.tokenContractAddress,
            "burn"
        ).open_some()
        sp.transfer(tokenContractParam, sp.mutez(0), contractHandle)

    def mintTokens(self, tokensToMint, address):
        sp.set_type(tokensToMint, sp.TNat)
        sp.set_type(address, sp.TAddress)

        tokenContractParam = sp.record(address= address, value= tokensToMint)
        contractHandle = sp.contract(
            sp.TRecord(address = sp.TAddress, value = sp.TNat),
            self.data.tokenContractAddress,
            "mint"
        ).open_some()
        sp.transfer(tokenContractParam, sp.mutez(0), contractHandle)

    # Calculate newly accrued stability fees with the given input.
    #
    # Parameters:
    # - ovenInterestIndex: The local interest index of the oven.
    # - borrowedTokens: The tokens borrowed from an oven.
    # - stabilityFeeTokens: The existing tokens that are part of the stability fee
    # - minterInterestIndex: The global interest index in the minter.
    @sp.private_lambda(with_storage="read-only")
    def calculateNewAccruedInterest(self, params):
        sp.set_type(params, sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))

        ovenInterestIndex =  sp.as_nat(sp.fst(params))
        borrowedTokens =     sp.fst(sp.snd(params))
        stabilityFeeTokens = sp.fst(sp.snd(sp.snd(params)))
        minterInterestIndex = sp.snd(sp.snd(sp.snd(params)))

        ratio = sp.fst(sp.ediv((minterInterestIndex * Constants.PRECISION), ovenInterestIndex).open_some())        
        totalPrinciple = borrowedTokens + stabilityFeeTokens
        newTotalTokens = sp.fst(sp.ediv((ratio * totalPrinciple), Constants.PRECISION).open_some())
        newTokensAccruedAsFee = sp.as_nat(newTotalTokens - totalPrinciple)
        sp.result(newTokensAccruedAsFee)


    # Compound interest via a linear approximation.
    #
    # Parameters:
    # - initialValue: The initial value to compound
    # - stabilityFee: The interest rate compounding is occuring at
    # - numPeriods: The number of periods to compound for
    # @sp.private_lambda(with_storage="read-only")
    # def compoundWithLinearApproximation2(self, params):
    #     sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))

    #     initialValue = sp.fst(params)
    #     stabilityFee = sp.fst(sp.snd(params))
    #     numPeriods = sp.snd(sp.snd(params))

    #     sp.result((initialValue * (Constants.PRECISION + (numPeriods * stabilityFee))) // Constants.PRECISION)

    # @sp.private_lambda(with_storage="read-only")
    # def compoundWithLinearApproximation(self, params):
    #     sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))

    #     myLambdaInlined = sp.build_lambda(self.func)
    #     sp.result(myLambdaInlined(params))  
        
    def compoundWithLinearApproximation_implementation(self, params):
        sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))

        initialValue = sp.fst(params)
        stabilityFee = sp.fst(sp.snd(params))
        numPeriods = sp.snd(sp.snd(params))

        # return (initialValue * (Constants.PRECISION + (numPeriods * stabilityFee))) // Constants.PRECISION
        sp.result((initialValue * (Constants.PRECISION + (numPeriods * stabilityFee))) // Constants.PRECISION)
        # sp.result(arg + 1)


    # TODO(keefertaylor): Figure out how to enable this mess.
    #     # internal = sp.build_lambda(self.compoundWithLinearApproximation)

    #     sp.result(12)

    # # Internal implementation of compoundWithLinearApproximation.
    # #
    # # Split into a function so that it can be reused in the private_lambda and the onchain_view, since onchain_views 
    # # cannot call private lambdas.
    # def compoundWithLinearApproximation(self, params):
    #     sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))

    #     initialValue = sp.fst(params)
    #     stabilityFee = sp.fst(sp.snd(params))
    #     numPeriods = sp.snd(sp.snd(params))

    #     return (initialValue * (Constants.PRECISION + (numPeriods * stabilityFee))) // Constants.PRECISION
    #     # sp.result((initialValue * (Constants.PRECISION + (numPeriods * stabilityFee))) // Constants.PRECISION)

    # Compute the collateralization percentage from the given inputs
    # Output is in the form of 200_000_000 (= 200%)
    @sp.private_lambda(with_storage="read-only")
    def computeCollateralizationPercentage(self, params):
        sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))

        ovenBalance = sp.fst(params)
        xtzPrice = sp.fst(sp.snd(params))
        borrowedTokens = sp.snd(sp.snd(params))

        # Compute collateral value.
        collateralValue = ovenBalance * xtzPrice // Constants.PRECISION
        ratio = (collateralValue * Constants.PRECISION) // (borrowedTokens)
        sp.result(ratio * 100)

    def updateOvenState(self, ovenAddress, borrowedTokens, stabilityFeeTokens, interestIndex, isLiquidated, sendAmount):
        sp.set_type(ovenAddress, sp.TAddress)
        sp.set_type(borrowedTokens, sp.TNat)
        sp.set_type(stabilityFeeTokens, sp.TNat)
        sp.set_type(interestIndex, sp.TNat)
        sp.set_type(isLiquidated, sp.TBool)
        sp.set_type(sendAmount, sp.TMutez)

        # Inform oven of new state.
        ovenContractParam = (ovenAddress, (borrowedTokens, (sp.to_int(stabilityFeeTokens), (sp.to_int(interestIndex), isLiquidated))))

        ovenHandle = sp.contract(
            OvenApi.UPDATE_STATE_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.UPDATE_STATE_ENTRY_POINT_NAME
        ).open_some()

        sp.transfer(ovenContractParam, sendAmount, ovenHandle)

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
    DevFund = sp.io.import_script_from_url("file:dev-fund.py")
    DummyContract = sp.io.import_script_from_url("file:test-helpers/dummy-contract.py")
    MockOvenProxy = sp.io.import_script_from_url("file:test-helpers/mock-oven-proxy.py")
    StabilityFund = sp.io.import_script_from_url("file:stability-fund.py")
    Token = sp.io.import_script_from_url("file:token.py")

    ################################################################
    # Helpers
    ################################################################

    # A Tester flass that wraps a lambda function to allow for unit testing.
    # See: https://smartpy.io/releases/20201220-f9f4ad18bd6ec2293f22b8c8812fefbde46d6b7d/ide?template=test_global_lambda.py
    # This should compute for views with a param.
    # TODO add tests for units
    # TODO doc this can also be used for views
    # TODO keefertaylor: Refactor this to be used everywhere in an imported file
    class Tester(sp.Contract):
        def __init__(self, f):
            self.f = f.f
            self.init(result = sp.none)

        # Compute the value of the given function if the funtion takes parameters.
        @sp.entry_point
        def compute(self, data, param):
            b = sp.bind_block()
            with b:
                self.f(sp.record(data = data), param)
            self.data.result = sp.some(b.value)

    ################################################################
    # calculateNewAccruedInterest
    ################################################################

    @sp.add_test(name="calculateNewAccruedInterest")
    def test():
        scenario = sp.test_scenario()
        minter = MinterContract()
        scenario += minter

        tester = Tester(minter.calculateNewAccruedInterest)
        scenario += tester

        scenario += tester.compute(
            data = minter.data,
            param = (sp.to_int(1 * Constants.PRECISION), (100 * Constants.PRECISION, (0 * Constants.PRECISION,  1100000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 10 * Constants.PRECISION)

        scenario += tester.compute(
            data = minter.data,
            param = (sp.int(1100000000000000000), (100 * Constants.PRECISION, (10 * Constants.PRECISION, 1210000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 11 * Constants.PRECISION)

        scenario += tester.compute(
            data = minter.data,
            param = (sp.to_int(1 * Constants.PRECISION), (100 * Constants.PRECISION, (0 * Constants.PRECISION,  1210000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 21 * Constants.PRECISION)

        scenario += tester.compute(
            data = minter.data,
            param = (sp.int(1100000000000000000), (100 * Constants.PRECISION, (0 * Constants.PRECISION,  1210000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 10 * Constants.PRECISION)

        scenario += tester.compute(
            data = minter.data,
            param = (sp.int(1210000000000000000), (100 * Constants.PRECISION, (10 * Constants.PRECISION, 1331000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 11 * Constants.PRECISION)

        scenario += tester.compute(
            data = minter.data,
            param = (sp.int(1100000000000000000), (100 * Constants.PRECISION, (0 * Constants.PRECISION,  1331000000000000000)))
        )
        scenario.verify(tester.data.result.open_some() == 21 * Constants.PRECISION)
        
    ################################################################
    # compoundWithLinearApproximation
    ################################################################
        
    @sp.add_test(name="compoundWithLinearApproximation")
    def test():
        scenario = sp.test_scenario()
        minter = MinterContract()
        scenario += minter

        tester = Tester(minter.compoundWithLinearApproximation)
        scenario += tester

        # Two periods back to back
        scenario += tester.compute(
            data = minter.data,
            param = (1 * Constants.PRECISION, (100000000000000000, 1))
        )
        scenario.verify(tester.data.result.open_some() == sp.nat(1100000000000000000))
        scenario += tester.compute(
            data = minter.data,
            param = (1100000000000000000,  (100000000000000000, 1))
        )
        scenario.verify(tester.data.result.open_some() == sp.nat(1210000000000000000))       

        # Two periods in one update
        scenario += tester.compute(
            data = minter.data,
            param = (1 * Constants.PRECISION, (100000000000000000, 2))
        )
        scenario.verify(tester.data.result.open_some() == sp.nat(1200000000000000000))       

    ###############################################################
    # Liquidate
    ###############################################################

    @sp.add_test(name="liquidate - successfully compounds interest and accrues fees")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a dummpy contract that acts as the liquidity pool
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND the liquidator has $1000 of tokens.
        liquidatorTokens = 1000 * Constants.PRECISION 
        mintForOvenOwnerParam = sp.record(address = liquidityPool.address, value = liquidatorTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = interimTokenAdministrator
        )

        # AND a Minter contract
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        ovenBorrowedTokens = 90 * Constants.PRECISION # $90 kUSD
        ovenStabilityFeeTokens = sp.to_int(10 * Constants.PRECISION) # 10 kUSD
        amountLoaned = liquidatorTokens + ovenBorrowedTokens + sp.as_nat(ovenStabilityFeeTokens) # 1100 = 1000 + 90 + 10
        stabilityFee = 100000000000000000 # 10%
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            tokenContractAddress = token.address,
            stabilityFee = stabilityFee, 
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = Constants.PRECISION,
            liquidityPoolContractAddress = liquidityPool.address,
            amountLoaned = amountLoaned,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = Addresses.GOVERNOR_ADDRESS
        )

        # WHEN liquidate is called on an undercollateralized oven with $100 of tokens outstanding
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenOwnerAddress = Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        interestIndex = sp.to_int(Constants.PRECISION)

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (ovenStabilityFeeTokens, (interestIndex, liquidityPool.address))))))))

        # AND one period has elapsed
        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = now,
        )

        # THEN an updated interest index is sent to the oven
        scenario.verify(ovenProxy.data.updateState_interestIndex == sp.to_int(minter.data.interestIndex))

        # AND all stability fees on the oven are repaid.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.int(0))

        # AND the minter compounded interest.
        scenario.verify(minter.data.interestIndex == 1100000000000000000)
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)

        # AND the liquidator received the collateral in the oven.
        scenario.verify(liquidityPool.balance == ovenBalanceMutez)

        # AND the liquidator is debited the correct number of tokens.
        expectedNewlyAccruedStabilityFees = 10 * Constants.PRECISION
        outstandingTokens = sp.as_nat(ovenStabilityFeeTokens) + ovenBorrowedTokens + expectedNewlyAccruedStabilityFees
        liquidationFee = (outstandingTokens * liquidationFeePercent) // Constants.PRECISION
        totalTokensPaid = outstandingTokens + liquidationFee
        scenario.verify(token.data.balances[liquidityPool.address].balance == sp.as_nat(liquidatorTokens - totalTokensPaid))

        # AND the oven is marked as liquidated with values cleared correctly.
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == 0)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == True)

        # AND the total borrowed amount was updated
        #
        # expectedAmountLoanedAfterInterestAccrual = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                                          = 1100 kUSD * (1 + (1 * 0.1))
        #                                          = 1100 kUSD * (1 + 0.1)
        #                                          = 1100 kUSD * 1.1
        #                                          = 1210 kUSD
        #
        # expectedAmountRepaidAgainstOven = (ovenBorrowedTokens + ovenStabilityFees) * (1 + (numPeriods * stabilityFee))
        #                                 = (90 kUSD + 10 kUSD) * (1 + (1 * 0.1))
        #                                 = 100 kUSD * (1 + 0.1)
        #                                 = 100 kUSD * 1.1
        #                                 = 110 kUSD
        #
        # expectedAmount = expectedAmountLoanedAfterInterestAccrual - expectedAmountRepaidAgainstOven
        #                = 1210 kUSD - 110 kUSD
        #                = 1100 kUSD
        expectedAmountLoanedAfterInterestAccrual = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedAmountLoanedAfterInterestAccrual == 1210000000000000000000) # 1210 kUSD

        amountExpectedToBeRepaidToOven = ((ovenBorrowedTokens + sp.as_nat(ovenStabilityFeeTokens)) * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(amountExpectedToBeRepaidToOven == 110000000000000000000) # 110 kUSD

        expectedAmountLoaned = sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountExpectedToBeRepaidToOven)
        scenario.verify(expectedAmountLoaned == 1100000000000000000000) # 1100 kUSD
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        #
        # expectedAmountPaidInLiquidationFees = amountRepaidAgainstOven * liquidationFee
        #                                     = 110 kUSD * 0.08
        #                                     = 8.8 kUSD
        #
        # expectedTotalValuePaidToFunds = newlyAccruedInterest + liquidationFee
        #                               = (expectedAmountLoanedAfterInterestAccrual - originalAmountLoaned) + liquidationFee
        #                               = (1210 kUSD - 1100 kUSD) + 8.8 kUSD
        #                               = 110 kUSD + 8.8 kUSD
        #                               = 118.8 kUSD
        #
        # expectedDevFundValue = totalValuePaidToFunds * devFundSplit
        #              = 118.8 kUSD * 0.1
        #              = 11.88 kUSD
        #
        # expectedStabilityFundValue = totalValuePaidToFunds - expectedDevFundValue
        #                            = 118.8 kUSD - 11.88 kUSD
        #                            = 106.92 kUSD
        expectedAmountPaidInLiquidationFees = (amountExpectedToBeRepaidToOven * liquidationFeePercent) // Constants.PRECISION
        scenario.verify(expectedAmountPaidInLiquidationFees == 8800000000000000000) # 8.8 kUSD

        expectedTotalValuePaidToFunds = sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned) + expectedAmountPaidInLiquidationFees
        scenario.verify(expectedTotalValuePaidToFunds == 118800000000000000000) # 118.8 kUSD

        expectedDevFundValue = (expectedTotalValuePaidToFunds * devFundSplit) // Constants.PRECISION
        scenario.verify(expectedDevFundValue == 11880000000000000000) # 11.88 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(expectedTotalValuePaidToFunds - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 106920000000000000000) # 106.92 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="liquidate - successfully liquidates undercollateralized oven")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND the liquidator has $1000 of tokens.
        liquidatorTokens = 1000 * Constants.PRECISION 
        mintForOvenOwnerParam = sp.record(address = liquidityPool.address, value = liquidatorTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = interimTokenAdministrator
        )

        # AND a Minter contract
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        ovenBorrowedTokens = 90 * Constants.PRECISION # $90 kUSD
        ovenStabilityFeeTokens = sp.to_int(10 * Constants.PRECISION) # 10 kUSD
        amountLoaned = liquidatorTokens + ovenBorrowedTokens + sp.as_nat(ovenStabilityFeeTokens) # 1100 = 1000 + 90 + 10
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            amountLoaned = amountLoaned,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = Addresses.GOVERNOR_ADDRESS
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = liquidityPool.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (ovenStabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(liquidityPool.balance == ovenBalanceMutez)

        # AND the liquidator is debited the correct number of tokens.
        outstandingTokens = sp.as_nat(ovenStabilityFeeTokens) + ovenBorrowedTokens
        liquidationFee = (outstandingTokens * liquidationFeePercent) // Constants.PRECISION
        totalTokensPaid = outstandingTokens + liquidationFee
        scenario.verify(token.data.balances[liquidityPool.address].balance == sp.as_nat(liquidatorTokens - totalTokensPaid))

        # AND the oven is marked as liquidated with values cleared correctly.
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == 0)
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == 0)
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == True)

        # AND the stability and dev funds receive a split of the liquidation fee and stability tokens
        # expectedAmountLoanedAfterInterestAccrual = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                                          = 1100 kUSD * (1 + (x * 0))
        #                                          = 1100 kUSD * (1 + 0)
        #                                          = 1100 kUSD * 1
        #                                          = 1100 kUSD
        #                                          = amountLoaned
        #
        # expectedAmountRepaidAgainstOven = (ovenBorrowedTokens + ovenStabilityFees) * (1 + (numPeriods * stabilityFee))
        #                                 = (90 kUSD + 10 kUSD) * (1 + (n * 0))
        #                                 = 100 kUSD * (1 + 0)
        #                                 = 100 kUSD * 1
        #                                 = 100 kUSD
        #                                 = (ovenBorrowedTokens + ovenStabilityFees)
        #
        # expectedNewlyAccruedInterest = expectedAmountLoanedAfterInterestAccrual  - originalLoanAmount
        #                              = 1100 kUSD - 1100 kUSD
        #                              = 0 kUSD
        # 
        # expectedAmountPaidInLiquidationFees = amountRepaidAgainstOven * liquidationFee
        #                                     = 100 kUSD * 0.08
        #                                     = 8 kUSD
        #
        # expectedTotalValuePaidToFunds = newlyAccruedInterest + liquidationFee
        #                               = 0 kUSD + 8 kUSD
        #                               = 8 kUSD
        #
        # expectedDevFundValue = totalValuePaidToFunds * devFundSplit
        #                      = 8 kUSD * 0.1
        #                      = 0.8 kUSD
        #
        # expectedStabilityFundValue = totalValuePaidToFunds - expectedDevFundValue
        #                            = 8 kUSD - 0.8 kUSD
        #                            = 7.2 kUSD
        expectedAmountLoanedAfterInterestAccrual = amountLoaned
        scenario.verify(expectedAmountLoanedAfterInterestAccrual == 1100000000000000000000) # 1000 kUSD

        expectedAmountRepaidAgainstOven = ovenBorrowedTokens + sp.as_nat(ovenStabilityFeeTokens)
        scenario.verify(expectedAmountRepaidAgainstOven == 100000000000000000000) # 100 kUSD

        expectedNewlyAccruedInterest = sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned)
        scenario.verify(expectedNewlyAccruedInterest == 0) # 0 kUSD

        expectedAmountPaidInLiquidationFees = (expectedAmountRepaidAgainstOven * liquidationFeePercent) // Constants.PRECISION
        scenario.verify(expectedAmountPaidInLiquidationFees == 8000000000000000000) # 8 kUSD

        expectedTotalValuePaidToFunds = expectedNewlyAccruedInterest + expectedAmountPaidInLiquidationFees
        scenario.verify(expectedTotalValuePaidToFunds == 8000000000000000000) # 8 kUSD

        expectedDevFundValue = (expectedTotalValuePaidToFunds * devFundSplit) // Constants.PRECISION
        scenario.verify(expectedDevFundValue == 800000000000000000) # 0.8 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(expectedTotalValuePaidToFunds - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 7200000000000000000) # 0.8 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)
    
    @sp.add_test(name="liquidate - fails if contract is not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND the liquidator has $1000 of tokens.
        liquidatorTokens = 1000 * Constants.PRECISION 
        mintForOvenOwnerParam = sp.record(address = liquidityPool.address, value = liquidatorTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = interimTokenAdministrator
        )

        # AND a Minter contract that is uninitialized
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        ovenBorrowedTokens = 90 * Constants.PRECISION # $90 kUSD
        ovenStabilityFeeTokens = sp.to_int(10 * Constants.PRECISION) # 10 kUSD
        amountLoaned = liquidatorTokens + ovenBorrowedTokens + sp.as_nat(ovenStabilityFeeTokens) # 1100 = 1000 + 90 + 10
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            amountLoaned = amountLoaned,
            initialized = False,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = Addresses.GOVERNOR_ADDRESS
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = liquidityPool.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (ovenStabilityFeeTokens, (interestIndex, liquidatorAddress))))))))

        # THEN the call fails with NOT_INITIALIZED
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
 
            valid = False,
            exception = Errors.NOT_INITIALIZED,
        )

    @sp.add_test(name="liquidate - liquidity pool can always liquidate")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND the liquidator has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = liquidityPool.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~181% collateralized
        ovenBorrowedTokens = 11 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = liquidityPool.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(liquidityPool.balance == ovenBalanceMutez)
 
    @sp.add_test(name="liquidate - stability fund can always liquidate")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND dummy contracts to act as the dev and stability funds.
        stabilityFund = DummyContract.DummyContract()
        scenario += stabilityFund

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%        
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            stabilityFundContractAddress = stabilityFund.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND the liquidator has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = stabilityFund.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~181% collateralized
        ovenBorrowedTokens = 11 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = stabilityFund.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(stabilityFund.balance == ovenBalanceMutez)

    @sp.add_test(name="liquidate - private owner cannot liquidate above private owner liquidation fee percent")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a dummy contract that acts as a private liquidator
        privateLiquidator = DummyContract.DummyContract()
        scenario += privateLiquidator

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%        
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND the liquidator has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = privateLiquidator.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~181% collateralized
        ovenBorrowedTokens = 11 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = privateLiquidator.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        
        # THEN the call will fail with NOT_ALLOWED_TO_LIQUIDATE
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_ALLOWED_TO_LIQUIDATE
        )

    @sp.add_test(name="liquidate - private owner can liquidate below private owner liquidation fee percent")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND dummy contracts to act as the dev and stability funds.
        stabilityFund = DummyContract.DummyContract()
        devFund = DummyContract.DummyContract()
        scenario += stabilityFund
        scenario += devFund

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a dummy contract that acts as a private liquidator
        privateLiquidator = DummyContract.DummyContract()
        scenario += privateLiquidator

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%        
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFundContractAddress = stabilityFund.address,
            developerFundContractAddress = devFund.address,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND the liquidator has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = privateLiquidator.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven.
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~166% collateralized
        ovenBorrowedTokens = 12 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = privateLiquidator.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(privateLiquidator.balance == ovenBalanceMutez)

    @sp.add_test(name="liquidate - liquidity pool can liquidate below private owner liquidation fee percent")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a liquidity pool contract
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress,
        )
        scenario += token

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a dummy contract that acts as a private liquidator
        privateLiquidator = DummyContract.DummyContract()
        scenario += privateLiquidator

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%        
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND the liquidator has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = liquidityPool.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven by the liquidity pool
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~166% collateralized
        ovenBorrowedTokens = 12 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = liquidityPool.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(liquidityPool.balance == ovenBalanceMutez)

    @sp.add_test(name="liquidate - stability fund can liquidate below private owner liquidation fee percent")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a liquidity pool contract
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress,
        )
        scenario += token

        # AND dummy contracts to act as the dev and stability funds.
        stabilityFund = DummyContract.DummyContract()
        scenario += stabilityFund

        # AND a dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND a dummy contract that acts as a private liquidator
        privateLiquidator = DummyContract.DummyContract()
        scenario += privateLiquidator

        # AND a Minter contract
        stabilityFee = sp.nat(0)
        liquidationFeePercent = sp.nat(80000000000000000) # 8%
        devFundSplit = sp.nat(100000000000000000) # 10%
        collateralizationPercentage = sp.nat(200000000000000000000) # 200%
        privateOwnerLiquidationThreshold = sp.nat(25000000000000000000) # 25%        
        minter = MinterContract(
            liquidationFeePercent = liquidationFeePercent,
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFundContractAddress = stabilityFund.address,
            tokenContractAddress = token.address,
            liquidityPoolContractAddress = liquidityPool.address,
            collateralizationPercentage = collateralizationPercentage,
            privateOwnerLiquidationThreshold = privateOwnerLiquidationThreshold,
            stabilityFee = stabilityFee,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND the stability fund has $1000 of tokens.
        ovenOwnerTokens = 1000 * Constants.PRECISION
        mintForOvenOwnerParam = sp.record(address = stabilityFund.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidate is called on an undercollateralized oven by the liquidity pool
        ovenBalance = Constants.PRECISION * 20 # 20 XTZ
        ovenBalanceMutez = sp.mutez(20 * 1000000) # 20 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        # Borrow Limit: 20 XTZ * 1 USD/XTZ / 200% collateralization = $10
        # Collateralization = (20 XTZ * $1 / XTZ USD) / $11 borrowed = ~166% collateralized
        ovenBorrowedTokens = 12 * Constants.PRECISION # $19 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = stabilityFund.address

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the liquidator received the collateral in the oven.
        scenario.verify(stabilityFund.balance == ovenBalanceMutez)                

    @sp.add_test(name="liquidate - fails when liquidator has too few tokens")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )    

        # AND a dummy contract that acts as the liquidator.
        liquidator = DummyContract.DummyContract()
        scenario += liquidator

        # AND the liquidator has $1 of tokens.
        ovenOwnerTokens = 1 * Constants.PRECISION 
        mintForOvenOwnerParam = sp.record(address = liquidator.address, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN liquidating an undecollateralized requires more tokens than the liquidator has.
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenBorrowedTokens = 2 * Constants.PRECISION # $2 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        isLiquidated = False

        stabilityFeeTokens = sp.to_int(Constants.PRECISION)
        interestIndex = sp.to_int(Constants.PRECISION)

        liquidatorAddress = liquidator.address

        # THEN the call fails with TOKEN_INSUFFICIENT_BALANCE
        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))
        scenario += minter.liquidate(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.TOKEN_INSUFFICIENT_BALANCE
        )

    @sp.add_test(name="liquidate - fails if oven is properly collateralized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND an Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            liquidityPoolContractAddress = liquidityPool.address,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # WHEN liquidate is called on an oven that exactly meets the collateralization ratios
        ovenBalance = 2 * Constants.PRECISION # 2 XTZ
        ovenBalanceMutez = sp.mutez(2000000) # 2 XTZ
        xtzPrice = Constants.PRECISION # 1 XTZ / $1
        ovenBorrowedTokens = 1 * Constants.PRECISION # $1 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        liquidatorAddress = liquidityPool.address

        stabilityFeeTokens = sp.to_int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        isLiquidated = False

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))

        # THEN the call fails with NOT_UNDER_COLLATERALIZED
        scenario += minter.liquidate(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_UNDER_COLLATERALIZED
        )

    @sp.add_test(name="liquidate - fails if oven is already liquidated")
    def test():
        scenario = sp.test_scenario()

        # GIVEN dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND an Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            liquidityPoolContractAddress = liquidityPool.address,
            amountLoaned = 9000 * Constants.PRECISION # 9,000 kUSD
        )
        scenario += minter

        # WHEN liquidate is called on an undercollateralized oven which is already liquidated
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenBorrowedTokens = 2 * Constants.PRECISION # $2 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        liquidatorAddress = liquidityPool.address

        stabilityFeeTokens = sp.to_int(Constants.PRECISION)
        interestIndex = sp.to_int(Constants.PRECISION)

        isLiquidated = True

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))

        # THEN the call fails with LIQUIDATED
        scenario += minter.liquidate(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.LIQUIDATED
        )

    @sp.add_test(name="liquidate - fails if not called by ovenProxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN dummy contract that acts as the liquidity pool.
        liquidityPool = DummyContract.DummyContract()
        scenario += liquidityPool

        # AND an Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            liquidityPoolContractAddress = liquidityPool.address,
        )
        scenario += minter

        # WHEN liquidate is called on an undercollateralized oven by someone other than the oven proxy
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ

        xtzPrice = Constants.PRECISION # 1 XTZ / $1

        ovenBorrowedTokens = 2 * Constants.PRECISION # $2 kUSD

        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        liquidatorAddress = liquidityPool.address

        stabilityFeeTokens = sp.to_int(Constants.PRECISION)
        interestIndex = sp.to_int(Constants.PRECISION)

        isLiquidated = False

        param = (xtzPrice, (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress))))))))

        # THEN the call fails with NOT_OVEN_PROXY
        notOvenProxy = Addresses.NULL_ADDRESS
        scenario += minter.liquidate(param).run(
            sender = notOvenProxy,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_OVEN_PROXY
        )

    ###############################################################
    # Repay
    ###############################################################

    @sp.add_test(name="repay - succeeds and compounds interest and stability fees correctly")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND an Minter contract
        amountLoaned = Constants.PRECISION * 5 # 5 kUSD
        stabilityFee = 100000000000000000 # 10%
        devFundSplit = sp.nat(100000000000000000) # 10%
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = Constants.PRECISION,
            amountLoaned = amountLoaned,
            devFundSplit = devFundSplit,
            tokenContractAddress = token.address,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND the owner has tokens to repay.
        tokensToRepay = Constants.PRECISION # 1 kUSD
        scenario += token.mint(
            sp.record(
                address = Addresses.OVEN_OWNER_ADDRESS,
                value = tokensToRepay
            )
        ).run(
            sender = minter.address
        )

        # WHEN repay is called with valid inputs
        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        ovenBorrowedTokens = 100 * Constants.PRECISION # $100 kUSD
        isLiquidated = False
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.to_int(Constants.PRECISION)

        param = (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.repay(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = now,
        )

        # THEN an updated interest index and stability fee is sent to the oven.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == ((10 * Constants.PRECISION) - tokensToRepay))
        scenario.verify(ovenProxy.data.updateState_interestIndex == sp.to_int(minter.data.interestIndex))

        # AND the minter compounded interest.
        scenario.verify(minter.data.interestIndex == 1100000000000000000)
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)

        # AND the total borrowed amount was updated
        # expectedAmount = (amountLoaned * (1 + (numPeriods * stabilityFee))) - newly repaid amount
        #                = (5 kUSD * (1 + (1 * 0.1))) - 1 kUSD
        #                = (5 kUSD * (1 + 0.1)) - 1 kUSD
        #                = (5 kUSD * 1.1) - 1 kUSD
        #                = 5.5 kUSD - 1 kUSD
        #                = 4.5 kUSD
        expectedAmountLoanedAfterInterestAccrual = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        expectedAmountLoaned = sp.as_nat(expectedAmountLoanedAfterInterestAccrual - tokensToRepay)
        scenario.verify(expectedAmountLoanedAfterInterestAccrual == 5500000000000000000) # 5.5 kUSD
        scenario.verify(expectedAmountLoaned == 4500000000000000000) # 4.5 kUSD = expectedAmountOfInterestAccrued + tokensToRepay
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (expectedAmountLoanedAfterInterestAccrual - oldAmountLoaned) * devFundSplit
        #              = (5.5 - 5) * .1
        #              = 0.5 * .1
        #              = 0.05
        # expectedStabilityFundValue = (expectedAmountLoanedAfterInterestAccrual - oldAmountLoaned) - expectedDevFundValue
        #                            = (5.5 - 5) - .05
        #                            = 0.5 - .05
        #                            = 0.45
        expectedDevFundValue = (sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned) * devFundSplit) //Constants.PRECISION
        scenario.verify(expectedDevFundValue == 50000000000000000) # 0.05 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 450000000000000000) # 0.45 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="repay - repays amount greater than stability fees")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a governor
        governorAddress = Addresses.GOVERNOR_ADDRESS

        # AND an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND an Oven owner
        ovenOwner = Addresses.OVEN_OWNER_ADDRESS

        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a Minter contract
        amountLoaned = sp.nat(8)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,
            stabilityFee = sp.nat(0),
            amountLoaned = amountLoaned,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = interimTokenAdministrator
        )

        # AND the oven owner has 100 tokens.
        ovenOwnerTokens = sp.nat(100)
        mintForOvenOwnerParam = sp.record(address = ovenOwner, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN repay is called with an amount greater than stability fees
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        ovenBorrowedTokens = sp.nat(12)
        isLiquidated = False
        stabilityFeeTokens = sp.int(4)
        interestIndex = sp.to_int(Constants.PRECISION)
        tokensToRepay = amountLoaned
        param = (ovenAddress, (ovenOwner, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the stability fees are set to zero.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.int(0))
        
        # AND the borrowed tokens is reduced by the remainder.
        expectedBorrowedTokens = sp.as_nat(ovenBorrowedTokens - sp.as_nat(tokensToRepay - sp.as_nat(stabilityFeeTokens)))
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == expectedBorrowedTokens)
        
        # AND the oven owner was debited the amount of tokens to repay.
        scenario.verify(token.data.balances[ovenOwner].balance == sp.as_nat(ovenOwnerTokens - tokensToRepay))

        # AND the other values are passed back to the the oven proxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)

        # AND the oven proxy received the balance of the oven.
        scenario.verify(ovenProxy.balance == ovenBalanceMutez)

    @sp.add_test(name="repay - repays amount less than stability fees")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a governor
        governorAddress = Addresses.GOVERNOR_ADDRESS

        # AND an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND an Oven owner
        ovenOwner =  Addresses.OVEN_OWNER_ADDRESS

        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a Minter contract
        ovenBorrowedTokens = sp.nat(12)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,
            stabilityFee = sp.nat(0),
            amountLoaned = ovenBorrowedTokens
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = interimTokenAdministrator
        )

        # AND the oven owner has 100 tokens.
        ovenOwnerTokens = sp.nat(100)
        mintForOvenOwnerParam = sp.record(address = ovenOwner, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN repay is called with an amount less than stability fees
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        isLiquidated = False
        stabilityFeeTokens = sp.int(5)
        interestIndex = sp.to_int(Constants.PRECISION)
        tokensToRepay = sp.nat(4)
        param = (ovenAddress, (ovenOwner, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the stability fees are reduced by the amount to repay and the borrowed tokens are the same.
        expectedStabilityFeeTokens = stabilityFeeTokens - sp.to_int(tokensToRepay)
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == expectedStabilityFeeTokens)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == ovenBorrowedTokens)
        
        # AND the oven owner was debited the amount of tokens to repay.
        scenario.verify(token.data.balances[ovenOwner].balance == sp.as_nat(ovenOwnerTokens - tokensToRepay))

        # AND the other values are passed back to the the oven proxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)

        # AND the oven proxy received the balance of the oven.
        scenario.verify(ovenProxy.balance == ovenBalanceMutez)

    @sp.add_test(name="repay - repays more tokens than owned")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a governor, oven proxy and oven owner address.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS

        # AND a Token contract.
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        ovenBorrowedTokens = sp.nat(12)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,
            stabilityFee = sp.nat(0),
            amountLoaned = ovenBorrowedTokens
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND the oven owner has 1 tokens.
        ovenOwnerTokens = sp.nat(1)
        mintForOvenOwnerParam = sp.record(address = ovenOwnerAddress, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN repay is called with for an amount greater than the amount owned THEN the call fails.
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        isLiquidated = False
        stabilityFeeTokens = sp.int(5)
        interestIndex = sp.to_int(Constants.PRECISION)

        tokensToRepay = 2 * ovenOwnerTokens

        param = (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    @sp.add_test(name="repay - fails if contract is not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a governor
        governorAddress = Addresses.GOVERNOR_ADDRESS

        # AND an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND an Oven owner
        ovenOwner =  Addresses.OVEN_OWNER_ADDRESS

        # AND a Token contract.
        interimTokenAdministrator = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = interimTokenAdministrator
        )
        scenario += token

        # AND a Minter contract that is uninitialized
        ovenBorrowedTokens = sp.nat(12)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,
            stabilityFee = sp.nat(0),
            amountLoaned = ovenBorrowedTokens,
            initialized = False,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = interimTokenAdministrator
        )

        # AND the oven owner has 100 tokens.
        ovenOwnerTokens = sp.nat(100)
        mintForOvenOwnerParam = sp.record(address = ovenOwner, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN repay is called with an amount less than stability fees
        # THEN the call fails with NOT_INITIALIZED
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        isLiquidated = False
        stabilityFeeTokens = sp.int(5)
        interestIndex = sp.to_int(Constants.PRECISION)
        tokensToRepay = sp.nat(4)
        param = (ovenAddress, (ovenOwner, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    @sp.add_test(name="repay - fails if repaying greater amount than owed")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a governor, oven proxy and oven owner address.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        ovenOwnerAddress =  Addresses.OVEN_OWNER_ADDRESS

        # AND a Token contract.
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        ovenBorrowedTokens = sp.nat(12)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,
            stabilityFee = sp.nat(0),
            amountLoaned = ovenBorrowedTokens
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND the oven owner has 100 tokens.
        ovenOwnerTokens = sp.nat(100)
        mintForOvenOwnerParam = sp.record(address = ovenOwnerAddress, value = ovenOwnerTokens)
        scenario += token.mint(mintForOvenOwnerParam).run(
            sender = minter.address
        )

        # WHEN repay is called with for an amount greater than is owed 
        # THEN the call fails with REPAID_MORE_THAN_OWED
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenBalance = Constants.PRECISION # 1 XTZ
        ovenBalanceMutez = sp.mutez(1000000) # 1 XTZ
        isLiquidated = False
        stabilityFeeTokens = sp.int(5)
        interestIndex = sp.to_int(Constants.PRECISION)

        tokensToRepay = 2 * (sp.as_nat(stabilityFeeTokens) + ovenBorrowedTokens)
        param = (ovenAddress, (ovenOwnerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.REPAID_MORE_THAN_OWED
        )

    @sp.add_test(name="repay - fails if oven is liquidated")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a Minter contract
        ovenBorrowedTokens = sp.nat(2)
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            amountLoaned = ovenBorrowedTokens
        )
        scenario += minter

        # WHEN repay is called from a liquidated oven 
        # THEN the call fails with LIQUIDATeD
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        ovenBalance = sp.nat(1)
        isLiquidated = True
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.to_int(Constants.PRECISION)
        tokensToRepay = sp.nat(1)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        scenario += minter.repay(param).run(
            sender = ovenProxy.address,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.LIQUIDATED
        )

    @sp.add_test(name="repay - fails if not called by oven proxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        ovenBorrowedTokens = sp.nat(2)
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
            amountLoaned = ovenBorrowedTokens
        )
        scenario += minter

        # WHEN repay is called by someone other than the oven proxy 
        # THEN the call fails with NOT_OVEN_PROXY
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        ovenBalance = sp.nat(1)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.to_int(Constants.PRECISION)
        tokensToRepay = sp.nat(1)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (ovenBorrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        notOvenProxyAddress = Addresses.NULL_ADDRESS
        scenario += minter.repay(param).run(
            sender = notOvenProxyAddress,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_OVEN_PROXY
        )

    ###############################################################
    # Borrow
    ###############################################################

    @sp.add_test(name="borrow - succeeds and accrues stability fees")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract.
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND an Minter contract
        amountLoaned = Constants.PRECISION * 5 # 5 kUSD
        stabilityFee = 100000000000000000 # 10%
        devFundSplit = sp.nat(100000000000000000) # 10%
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = Constants.PRECISION,
            amountLoaned = amountLoaned,
            devFundSplit = devFundSplit,
            tokenContractAddress = token.address,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN borrow is called with valid inputs
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 300 * Constants.PRECISION # 300 XTZ / $300
        ovenBalanceMutez = sp.mutez(300000000) # 300 XTZ / $300

        borrowedTokens =  100 * Constants.PRECISION # $100 kUSD

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION # 1 kUSD

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))

        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.borrow(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = now,
        )

        # THEN an updated interest index and stability fee is sent to the oven.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.to_int(10 * Constants.PRECISION))
        scenario.verify(ovenProxy.data.updateState_interestIndex == sp.to_int(minter.data.interestIndex))

        # AND the minter compounded interest.
        scenario.verify(minter.data.interestIndex == 1100000000000000000)
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)

        # AND the total borrowed amount was updated
        # expectedAmount = (amountLoaned * (1 + (numPeriods * stabilityFee))) - newly borrowed amount
        #                = (5 kUSD * (1 + (1 * 0.1))) + 1 kUSD
        #                = (5 kUSD * (1 + 0.1)) + 1 kUSD
        #                = (5 kUSD * 1.1) + 1 kUSD
        #                = 5.5 kUSD + 1 kUSD
        #                = 6.5 kUSD
        expectedAmountLoanedAfterInterestAccrual = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        expectedAmountLoaned = expectedAmountLoanedAfterInterestAccrual + tokensToBorrow
        scenario.verify(expectedAmountLoanedAfterInterestAccrual == 5500000000000000000) # 5.5 kUSD
        scenario.verify(expectedAmountLoaned == 6500000000000000000) # 6.5 kUSD = expectedAmountOfInterestAccrued + tokensToBorrow
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (expectedAmountLoanedAfterInterestAccrual - oldAmountLoaned) * devFundSplit
        #              = (5.5 - 5) * .1
        #              = 0.5 * .1
        #              = 0.05
        # expectedStabilityFundValue = (expectedAmountLoanedAfterInterestAccrual - oldAmountLoaned) - expectedDevFundValue
        #                            = (5.5 - 5) - .05
        #                            = 0.5 - .05
        #                            = 0.45
        expectedDevFundValue = (sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned) * devFundSplit) //Constants.PRECISION
        scenario.verify(expectedDevFundValue == 50000000000000000) # 0.05 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoanedAfterInterestAccrual - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 450000000000000000) # 0.45 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="borrow - succeeds and mints tokens")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN borrow is called with valid inputs representing some tokens which are already borrowed.
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 4 * Constants.PRECISION # 4 XTZ / $4
        ovenBalanceMutez = sp.mutez(2000000) # 4 XTZ / $4

        borrowedTokens = Constants.PRECISION # $1 kUSD

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION # $1 kUSD

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))
        scenario += minter.borrow(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN tokens are minted to the owner
        scenario.verify(token.data.balances[ownerAddress].balance == tokensToBorrow)

        # AND the rest of the params are passed back to the oven proxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == (borrowedTokens + tokensToBorrow))
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == stabilityFeeTokens)

        # AND the remaining balance is passed back to the oven proxy
        scenario.verify(ovenProxy.balance == ovenBalanceMutez)

    @sp.add_test(name="borrow - succeeds and mints tokens when zero tokens are outstanding")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN borrow is called with valid inputs and no tokens borrowed
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 2 * Constants.PRECISION # 2 XTZ / $2
        ovenBalanceMutez = sp.mutez(2000000) # 2 XTZ / $2

        borrowedTokens = sp.nat(0)

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))
        scenario += minter.borrow(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN tokens are minted to the owner
        scenario.verify(token.data.balances[ownerAddress].balance == tokensToBorrow)

        # AND the rest of the params are passed back to the oven proxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == tokensToBorrow)
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == stabilityFeeTokens)

        # AND the remaining balance is passed back to the oven proxy
        scenario.verify(ovenProxy.balance == ovenBalanceMutez)

    @sp.add_test(name="borrow - fails if contract is not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract that is uninitialized
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            tokenContractAddress = token.address,
            initialized = False,
        )
        scenario += minter

        # AND the Minter is the Token administrator
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN borrow is called with valid inputs representing some tokens which are already borrowed.
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 4 * Constants.PRECISION # 4 XTZ / $4
        ovenBalanceMutez = sp.mutez(2000000) # 4 XTZ / $4

        borrowedTokens = Constants.PRECISION # $1 kUSD

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION # $1 kUSD

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))

        # THEN the call fails with NOT_INITIALIZED
        scenario += minter.borrow(param).run(
            sender = ovenProxy.address,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    @sp.add_test(name="borrow - Fails if oven is undercollateralized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
        )
        scenario += minter

        # WHEN borrow is called with an amount that will undercollateralize the oven.
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 2 * Constants.PRECISION # 2 XTZ / $2
        ovenBalanceMutez = sp.mutez(2000000) # 2 XTZ / $2

        borrowedTokens = sp.nat(0)

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = ovenBalance

        # THEN the call fails.
        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))
        scenario += minter.borrow(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    @sp.add_test(name="borrow - fails if oven is liquidated")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
        )
        scenario += minter

        # WHEN borrow is called from a liquidated Oven.
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS

        isLiquidated = True

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 2 * Constants.PRECISION # 2 XTZ / $2
        ovenBalanceMutez = sp.mutez(2000000) # 2 XTZ / $2

        borrowedTokens = sp.nat(0)

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))

        # THEN the call fails
        scenario += minter.borrow(param).run(
            sender = ovenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    @sp.add_test(name="borrow - fails when not called by ovenProxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress,
        )
        scenario += minter

        # WHEN borrow is called by someone other than the OvenProxy
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS

        isLiquidated = True

        xtzPrice = Constants.PRECISION # $1 / XTZ
        ovenBalance = 2 * Constants.PRECISION # 2 XTZ / $2
        ovenBalanceMutez = sp.mutez(2000000) # 2 XTZ / $2

        borrowedTokens = sp.nat(0)

        interestIndex = sp.to_int(Constants.PRECISION)
        stabilityFeeTokens = sp.int(0)

        tokensToBorrow = Constants.PRECISION

        param = (xtzPrice, (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow))))))))

        notOvenProxyAddress = Addresses.NULL_ADDRESS

        # THEN the call fails
        scenario += minter.borrow(param).run(
            sender = notOvenProxyAddress,
            amount = ovenBalanceMutez,
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    ################################################################
    # Withdraw
    ################################################################

    @sp.add_test(name="withdraw - succeeds and compounds interest and stability fees correctly")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND an Minter contract
        amountLoaned = Constants.PRECISION * 5 # 5 kUSD
        stabilityFee = 100000000000000000 # 10%
        devFundSplit = sp.nat(100000000000000000) # 10%
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = Constants.PRECISION,
            amountLoaned = amountLoaned,
            devFundSplit = devFundSplit,
            tokenContractAddress = token.address,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND given inputs that represent a properly collateralized oven at a 200% collateralization ratio
        xtzPrice = 2 * Constants.PRECISION # $2 / XTZ
        borrowedTokens = 100 * Constants.PRECISION # $100 kUSD
        lockedCollateralMutez = sp.mutez(2100000000) # 210XTZ / $210
        lockedCollateral = 210 * Constants.PRECISION # 219 XTZ / $210

        # WHEN withdraw is called with an amount that does not under collateralize the oven
        amountToWithdrawMutez = sp.mutez(1)  
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenOwnerAddress = Addresses.OVEN_OWNER_ADDRESS
        isLiquidated = False
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.to_int(Constants.PRECISION)
        param = (
            xtzPrice, (
                ovenAddress, (
                    ovenOwnerAddress, (
                        lockedCollateral, (
                            borrowedTokens, (
                                isLiquidated, (
                                    stabilityFeeTokens, (
                                        interestIndex, amountToWithdrawMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.withdraw(param).run(
            sender = ovenProxy.address,
            amount = lockedCollateralMutez,
            now = now,
        )

        # THEN an updated interest index and stability fee is sent to the oven.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.to_int(10 * Constants.PRECISION))
        scenario.verify(ovenProxy.data.updateState_interestIndex == sp.to_int(minter.data.interestIndex))

        # AND the minter compounded interest.
        scenario.verify(minter.data.interestIndex == 1100000000000000000)
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)

        # AND the total borrowed amount was updated
        # expectedAmount = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                = 5 kUSD * (1 + (1 * 0.1))
        #                = 5 kUSD * (1 + 0.1)
        #                = 5 kUSD * 1.1
        #                = 5.5 kUSD
        expectedAmountLoaned = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedAmountLoaned == 5500000000000000000) # 5.5 kUSD
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (newAmountLoaned - oldAmountLoaned) * devFundSplit
        #              = (5.5 - 5) * .1
        #              = .5 * .1
        #              = .05
        # expectedStabilityFundValue = (newAmountLoaned - oldAmountLoaned) - expectedDevFundValue
        #                            = (5.5 - 5) - .05
        #                            = .5 - .05
        #                            = .45
        expectedDevFundValue = (sp.as_nat(expectedAmountLoaned - amountLoaned) * devFundSplit) //Constants.PRECISION
        scenario.verify(expectedDevFundValue == 50000000000000000) # 0.05 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoaned - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 450000000000000000) # 0.45 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="withdraw - Able to withdraw")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address
        )
        scenario += minter

        # AND a dummy contract that acts as the Oven owner
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # AND given inputs that represent a properly collateralized oven at a 200% collateralization ratio
        xtzPrice = 1 * Constants.PRECISION # $1 / XTZ
        borrowedTokens = 10 * Constants.PRECISION # $10 kUSD
        lockedCollateralMutez = sp.mutez(21000000) # 21XTZ / $21
        lockedCollateral = 21 * Constants.PRECISION # 21 XTZ / $21

        # WHEN withdraw is called with an amount that does not under collateralize the oven
        amountToWithdrawMutez = sp.mutez(1000000) # 1 XTZ / $1 
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenOwnerAddress = dummyContract.address
        isLiquidated = False
        param = (
            xtzPrice, (
                ovenAddress, (
                    ovenOwnerAddress, (
                        lockedCollateral, (
                            borrowedTokens, (
                                isLiquidated, (
                                    sp.int(0), (
                                        sp.to_int(Constants.PRECISION), amountToWithdrawMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.withdraw(param).run(
            sender = ovenProxy.address,
            amount = lockedCollateralMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the oven owner receives the withdrawal
        scenario.verify(dummyContract.balance == amountToWithdrawMutez)

        # AND the OvenProxy received the remainder of the collateral with correct values
        scenario.verify(ovenProxy.balance == (lockedCollateralMutez - amountToWithdrawMutez))
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)

    @sp.add_test(name="withdraw - Able to withdraw with zero borrowed tokens")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address
        )
        scenario += minter

        # AND a dummy contract that acts as the Oven owner
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # AND given inputs that represent a properly collateralized oven with zero tokens borrowed
        xtzPrice = 1 * Constants.PRECISION # $1 / XTZ
        borrowedTokens = sp.nat(0) # $0 kUSD
        lockedCollateralMutez = sp.mutez(21000000) # 21XTZ / $21
        lockedCollateral = 21 * Constants.PRECISION # 21 XTZ / $21

        # WHEN withdraw is called
        amountToWithdrawMutez = sp.mutez(1000000) # 1 XTZ / $1 
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenOwnerAddress = dummyContract.address
        isLiquidated = False
        param = (
            xtzPrice, (
                ovenAddress, (
                    ovenOwnerAddress, (
                        lockedCollateral, (
                            borrowedTokens, (
                                isLiquidated, (
                                    sp.int(0), (
                                        sp.to_int(Constants.PRECISION), amountToWithdrawMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.withdraw(param).run(
            sender = ovenProxy.address,
            amount = lockedCollateralMutez,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the oven owner receives the withdrawal
        scenario.verify(dummyContract.balance == amountToWithdrawMutez)

        # AND the OvenProxy received the remainder of the collateral with correct values
        scenario.verify(ovenProxy.balance == (lockedCollateralMutez - amountToWithdrawMutez))
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == isLiquidated)        

    @sp.add_test(name="withdraw - Fails if contract is not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy contract
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy
        
        # AND a Minter contract that is uninitialized
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            initialized = False,
        )
        scenario += minter

        # AND a dummy contract that acts as the Oven owner
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # AND given inputs that represent a properly collateralized oven at a 200% collateralization ratio
        xtzPrice = 1 * Constants.PRECISION # $1 / XTZ
        borrowedTokens = 10 * Constants.PRECISION # $10 kUSD
        lockedCollateralMutez = sp.mutez(21000000) # 21XTZ / $21
        lockedCollateral = 21 * Constants.PRECISION # 21 XTZ / $21

        # WHEN withdraw is called with an amount that does not under collateralize the oven
        amountToWithdrawMutez = sp.mutez(1000000) # 1 XTZ / $1 
        ovenAddress = Addresses.OVEN_ADDRESS
        ovenOwnerAddress = dummyContract.address
        isLiquidated = False
        param = (
            xtzPrice, (
                ovenAddress, (
                    ovenOwnerAddress, (
                        lockedCollateral, (
                            borrowedTokens, (
                                isLiquidated, (
                                    sp.int(0), (
                                        sp.to_int(Constants.PRECISION), amountToWithdrawMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )

        # THEN the call fails with NOT_INITIALIZED
        scenario += minter.withdraw(param).run(
            sender = ovenProxy.address,
            amount = lockedCollateralMutez,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    @sp.add_test(name="withdraw - fails when withdraw will undercollateralize oven")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # AND given inputs that represent a properly collateralized oven at a 200% collateralization ratio
        xtzPrice = 1 * Constants.PRECISION # $1 / XTZ
        borrowedTokens = 10 * Constants.PRECISION # $10 kUSD
        lockedCollateralMutez = sp.mutez(21000000) # 21XTZ / $21
        lockedCollateral = 21 * Constants.PRECISION # 21 XTZ / $21

        # WHEN withdraw is called with an amount that under collateralizes the oven THEN the call fails
        amountToWithdrawMutez = sp.mutez(10000000) # 10 XTZ / $10
        param = (
            xtzPrice, (
                sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                    sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                        lockedCollateral, (
                            borrowedTokens, (
                                False, (
                                    sp.int(4), (
                                        sp.int(5), amountToWithdrawMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.withdraw(param).run(
            sender = ovenProxyAddress,
            valid = False,
            amount = lockedCollateralMutez,
            now = sp.timestamp_from_utc_now(),
        )

    @sp.add_test(name="withdraw - fails when withdraw is greater than amount")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN withdraw is called from an with a greater amount than collateral is available THEN the call fails
        amountMutez = sp.mutez(10)
        amount = 10 * Constants.PRECISION
        withdrawAmountMutez = sp.mutez(20)
        param = (
            sp.nat(1), (
                sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                    sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                        amount, (
                            sp.nat(3), (
                                False, (
                                    sp.int(4), (
                                        sp.int(5), withdrawAmountMutez
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.withdraw(param).run(
            sender = ovenProxyAddress,
            valid = False,
            amount = amountMutez,
            now = sp.timestamp_from_utc_now(),
        )

    @sp.add_test(name="withdraw - succeeds even if when oven is liquidated")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN withdraw is called from an with a liquidated oven THEN the call fails.
        isLiquidated = True
        param = (
            Constants.PRECISION, (
                sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                    sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (
                        Constants.PRECISION, (
                            sp.nat(0), (
                                isLiquidated, (
                                    sp.int(0), (
                                        sp.to_int(Constants.PRECISION), sp.mutez(1)
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.withdraw(param).run(
            sender = ovenProxyAddress,
            now = sp.timestamp_from_utc_now(),
            amount = sp.mutez(1000000)
        )

    @sp.add_test(name="withdraw - fails when not called by oven proxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN withdraw is called from an address other than the OvenProxy THEN the call fails
        notOvenProxyAddress = Addresses.NULL_ADDRESS
        param = (sp.nat(1), (notOvenProxyAddress, (notOvenProxyAddress, (sp.nat(2), (sp.nat(3), (False, (sp.int(4), (sp.int(5), sp.mutez(6)))))))))
        scenario += minter.withdraw(param).run(
            sender = notOvenProxyAddress,
            valid = False,
            now = sp.timestamp_from_utc_now(),
        )

    ################################################################
    # Deposit
    ################################################################

    @sp.add_test(name="deposit - succeeds and compoounds interest and stability fees correctly")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND an Minter contract
        amountLoaned = Constants.PRECISION * 5 # 5 kUSD
        stabilityFee = 100000000000000000 # 10%
        devFundSplit = sp.nat(100000000000000000) # 10%
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = Constants.PRECISION,
            amountLoaned = amountLoaned,
            devFundSplit = devFundSplit,
            tokenContractAddress = token.address,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN deposit is called
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.to_int(Constants.PRECISION)
        borrowedTokens = 100 * Constants.PRECISION # $100 kUSD
        balance = sp.mutez(1000000) # 1 XTZ
        balanceNat = Constants.PRECISION
        param = (
            ovenAddress, (
                ownerAddress, (
                    balanceNat, (
                        borrowedTokens, (
                            False, (
                                stabilityFeeTokens,
                                interestIndex
                            )
                        )
                    )
                )
            )
        )
        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.deposit(param).run(
            amount = balance,
            sender = ovenProxy.address,
            now = now
        )

        # THEN an updated interest index and stability fee is sent to the oven.
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.to_int(10 * Constants.PRECISION))
        scenario.verify(ovenProxy.data.updateState_interestIndex == sp.to_int(minter.data.interestIndex))

        # AND the minter compounded interest.
        scenario.verify(minter.data.interestIndex == 1100000000000000000)
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)

        # AND the total borrowed amount was updated
        # expectedAmount = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                = 5 kUSD * (1 + (1 * 0.1))
        #                = 5 kUSD * (1 + 0.1)
        #                = 5 kUSD * 1.1
        #                = 5.5 kUSD
        expectedAmountLoaned = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedAmountLoaned == 5500000000000000000) # 5.5 kUSD
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (newAmountLoaned - oldAmountLoaned) * devFundSplit
        #              = (5.5 - 5) * .1
        #              = .5 * .1
        #              = .05
        # expectedStabilityFundValue = (newAmountLoaned - oldAmountLoaned) - expectedDevFundValue
        #                            = (5.5 - 5) - .05
        #                            = .5 - .05
        #                            = .45
        expectedDevFundValue = (sp.as_nat(expectedAmountLoaned - amountLoaned) * devFundSplit) //Constants.PRECISION
        scenario.verify(expectedDevFundValue == 50000000000000000) # 0.05 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoaned - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 450000000000000000) # 0.45 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="deposit - succeeds")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND an Minter contract
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address
        )
        scenario += minter

        # WHEN deposit is called
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        balance = sp.mutez(1)
        balanceNat = sp.nat(1)
        borrowedTokens = sp.nat(2)
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.int(1000000000000000000)
        param = (
            ovenAddress, (
                ownerAddress, (
                    balanceNat, (
                        borrowedTokens, (
                            False, (
                                stabilityFeeTokens,
                                interestIndex
                            )
                        )
                    )
                )
            )
        )
        scenario += minter.deposit(param).run(
            amount = balance,
            sender = ovenProxy.address,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN input parameters are propagated to the OvenProxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == False)
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.int(0))
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)

        # AND the mutez balance is sent to the oven proxy
        scenario.verify(ovenProxy.balance == balance)

    @sp.add_test(name="deposit - succeeds with no oven limit")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND an Minter contract with no oven max.
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
        )
        scenario += minter

        # WHEN deposit is called 
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        balance = sp.mutez(100000001) # 100.000001 XTZ
        balanceNat = sp.nat(100000001000000000000) # 100.000001 XTZ
        borrowedTokens = sp.nat(2)
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.int(1000000000000000000)
        param = (
            ovenAddress, (
                ownerAddress, (
                    balanceNat, (
                        borrowedTokens, (
                            False, (
                                stabilityFeeTokens,
                                interestIndex
                            )
                        )
                    )
                )
            )
        )   
        scenario += minter.deposit(param).run(
            amount = balance,
            sender = ovenProxy.address,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN input parameters are propagated to the OvenProxy
        scenario.verify(ovenProxy.data.updateState_ovenAddress == ovenAddress)
        scenario.verify(ovenProxy.data.updateState_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxy.data.updateState_isLiquidated == False)
        scenario.verify(ovenProxy.data.updateState_stabilityFeeTokens == sp.int(0))
        scenario.verify(ovenProxy.data.updateState_interestIndex == interestIndex)

        # AND the mutez balance is sent to the oven proxy
        scenario.verify(ovenProxy.balance == balance)

    @sp.add_test(name="deposit - fails if not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenProxy
        ovenProxy = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxy

        # AND a Minter contract that is uninitialized
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxy.address,
            initialized = False,
        )
        scenario += minter

        # WHEN deposit is called
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        balance = sp.mutez(1)
        balanceNat = sp.nat(1)
        borrowedTokens = sp.nat(2)
        stabilityFeeTokens = sp.int(0)
        interestIndex = sp.int(1000000000000000000)
        param = (
            ovenAddress, (
                ownerAddress, (
                    balanceNat, (
                        borrowedTokens, (
                            False, (
                                stabilityFeeTokens,
                                interestIndex
                            )
                        )
                    )
                )
            )
        )

        # THEN the call fails with NOT_INITIALIZED
        scenario += minter.deposit(param).run(
            amount = balance,
            sender = ovenProxy.address,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    @sp.add_test(name="deposit - fails when oven is liquidated")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN deposit is called from an with a liquidated oven THEN the call fails.
        isLiquidated = True
        param = (sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"), (sp.nat(1), (sp.nat(2), (isLiquidated, (sp.int(3), (sp.int(4))))))))
        scenario += minter.deposit(param).run(
            sender = ovenProxyAddress,
            valid = False,
            now = sp.timestamp_from_utc_now(),
        )

    @sp.add_test(name="deposit - fails when not called by oven proxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN deposit is called from an address other than the OvenProxy THEN the call fails
        notOvenProxyAddress = Addresses.NULL_ADDRESS
        param = (notOvenProxyAddress, (notOvenProxyAddress, (sp.nat(1), (sp.nat(2), (False, (sp.int(3), (sp.int(4))))))))
        scenario += minter.deposit(param).run(
            sender = notOvenProxyAddress,
            valid = False,
            now = sp.timestamp_from_utc_now(),
        )

    ################################################################
    # getInterestIndex
    ################################################################

    @sp.add_test(name="getInterestIndex - compounds interest and calls back")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a Minter contract
        initialInterestIndex = Constants.PRECISION
        stabilityFee = 100000000000000000 # 10%
        initialTime = sp.timestamp(0)
        amountLoaned = 1 * Constants.PRECISION # 1 kUSD
        devFundSplit = 100000000000000000 # 10%
        minter = MinterContract(
            interestIndex = initialInterestIndex,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = initialTime,
            devFundSplit = devFundSplit,

            tokenContractAddress = token.address,

            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,

            amountLoaned = amountLoaned
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # AND a dummy contract to receive the callback.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN getInterestIndex is called
        callback = sp.contract(sp.TNat, dummyContract.address, "natCallback").open_some()
        onePeriodLater = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
        scenario += minter.getInterestIndex(callback).run(
            now = onePeriodLater,
        )

        # THEN interest index is updated in the minter
        # expectedInterestIndex = initialIndex * (1 + (numPeriods * stabilityFee))
        #                       = 1.0 * (1 + (1 * 0.1))
        #                       = 1.0 * (1 + 0.1)
        #                       = 1.0 * 1.1
        #                       = 1.1
        expectedInterestIndex = (initialInterestIndex * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedInterestIndex == 1100000000000000000)
        scenario.verify(minter.data.interestIndex == expectedInterestIndex)

        # And the last update time is increased.
        scenario.verify(minter.data.lastInterestIndexUpdateTime == onePeriodLater)

        # AND the total borrowed amount was updated
        # expectedAmount = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                = 1 kUSD * (1 + (1 * 0.1))
        #                = 1 kUSD * (1 + 0.1)
        #                = 1 kUSD * 1.1
        #                = 1.1 kUSD
        expectedAmountLoaned = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedAmountLoaned == 1100000000000000000) # 1.1 kUSD
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (newAmountLoaned - oldAmountLoaned) * devFundSplit
        #              = (1.1 - 1) * 0.1
        #              = 0.1 * 0.1
        #              = 0.01
        #
        # expectedStabilityFundValue = (newAmountLoaned - oldAmountLoaned) - expectedDevFundValue
        #                            = (1.1 - 1) - 0.01
        #                            = 0.1 - .01
        #                            = 0.09
        expectedDevFundValue = (sp.as_nat(expectedAmountLoaned - amountLoaned) * devFundSplit) // Constants.PRECISION
        scenario.verify(expectedDevFundValue == 10000000000000000) # 0.01 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoaned - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 90000000000000000) # 0.09 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

        # AND the callback returned the correct value.
        scenario.verify(dummyContract.data.natValue == minter.data.interestIndex)

    @sp.add_test(name="getInterestIndex - fails if not initialized")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract that is not initialized
        minter = MinterContract(
            initialized = False,
        )
        scenario += minter

        # AND a dummy contract to receive the callback.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN getInterestIndex is called with an amount 
        # THEN the call fails with NOT_INITIALIZED
        callback = sp.contract(sp.TNat, dummyContract.address, "natCallback").open_some()
        scenario += minter.getInterestIndex(callback).run(
            amount = sp.mutez(1),
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    @sp.add_test(name="getInterestIndex - fails with amount")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        minter = MinterContract()
        scenario += minter

        # AND a dummy contract to receive the callback.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN getInterestIndex is called with an amount 
        # THEN the call fails with AMOUNT_NOT_ALLOWED
        callback = sp.contract(sp.TNat, dummyContract.address, "natCallback").open_some()
        scenario += minter.getInterestIndex(callback).run(
            amount = sp.mutez(1),
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.AMOUNT_NOT_ALLOWED
        )

    ################################################################
    # setGovernorContract
    ################################################################
    
    @sp.add_test(name="setGovernorContract - updates governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress
        )
        scenario += minter

        # WHEN setGovernorContract is called by the governor
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setGovernorContract(newGovernorContractAddress).run(
            sender = governorAddress,
        )

        # THEN the governor is updated.
        scenario.verify(minter.data.governorContractAddress == newGovernorContractAddress)

    @sp.add_test(name="setGovernorContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress
        )
        scenario += minter

        # WHEN setGovernorContract is called by someone other than the governor
        # THEN the request fails
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setGovernorContract(newGovernorContractAddress).run(
            sender = notGovernor,
            valid = False
        )

    ################################################################
    # setTokenContract
    ################################################################
    
    @sp.add_test(name="setTokenContract - updates token")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        tokenContractAddress = Addresses.TOKEN_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            tokenContractAddress = tokenContractAddress
        )
        scenario += minter

        # WHEN setTokenContract is called by the governor
        newTokenContractAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setTokenContract(newTokenContractAddress).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )

        # THEN the token contract is updated.
        scenario.verify(minter.data.tokenContractAddress == newTokenContractAddress)

    @sp.add_test(name="setTokenContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        tokenContractAddress = Addresses.TOKEN_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            tokenContractAddress = tokenContractAddress
        )
        scenario += minter

        # WHEN setTokenContract is called by someone other than the governor
        # THEN the request fails
        newTokenContractAddress = Addresses.ROTATED_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setTokenContract(newTokenContractAddress).run(
            sender = notGovernor,
            valid = False
        )

    ################################################################
    # setOvenProxyContract
    ################################################################
    
    @sp.add_test(name="setOvenProxyContract - updates oven proxy")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN setOvenProxyContract is called by the governor
        newOvenProxyContractAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setOvenProxyContract(newOvenProxyContractAddress).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )

        # THEN the oven proxy contract is updated.
        scenario.verify(minter.data.ovenProxyContractAddress == newOvenProxyContractAddress)

    @sp.add_test(name="setOvenProxyContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        ovenProxyAddress = Addresses.OVEN_PROXY_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            ovenProxyContractAddress = ovenProxyAddress
        )
        scenario += minter

        # WHEN setOvenProxyContract is called by someone other than the governor
        # THEN the request fails
        newOvenProxyContractAddress = Addresses.ROTATED_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setOvenProxyContract(newOvenProxyContractAddress).run(
            sender = notGovernor,
            valid = False
        )        

    ################################################################
    # setStabilityFundContract
    ################################################################
    
    @sp.add_test(name="setStabilityFundContract - updates stability fund")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            stabilityFundContractAddress = stabilityFundContractAddress
        )
        scenario += minter

        # WHEN setStabilityFundContract is called by the governor
        newStabilityFundAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setStabilityFundContract(newStabilityFundAddress).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )

        # THEN the stability fund contract is updated.
        scenario.verify(minter.data.stabilityFundContractAddress == newStabilityFundAddress)

    @sp.add_test(name="setStabilityFundContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS
        minter = MinterContract(
            governorContractAddress = Addresses.GOVERNOR_ADDRESS,
            stabilityFundContractAddress = stabilityFundContractAddress
        )
        scenario += minter

        # WHEN setStabilityFundContract is called by someone other than the governor
        # THEN the request fails
        newStabilityFundAddress = Addresses.ROTATED_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setStabilityFundContract(newStabilityFundAddress).run(
            sender = notGovernor,
            valid = False
        ) 

    ################################################################
    # setDeveloperFundContract
    ################################################################
    
    @sp.add_test(name="setDeveloperFundContract - updates developer fund")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS
        minter = MinterContract(
            developerFundContractAddress = developerFundContractAddress,
            governorContractAddress = Addresses.GOVERNOR_ADDRESS
        )
        scenario += minter

        # WHEN setDeveloperFundContract is called by the governor
        newDeveloperFundAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setDeveloperFundContract(newDeveloperFundAddress).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )

        # THEN the developer fund contract is updated.
        scenario.verify(minter.data.developerFundContractAddress == newDeveloperFundAddress)

    @sp.add_test(name="setDeveloperFundContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS
        minter = MinterContract(
            developerFundContractAddress = developerFundContractAddress,
            governorContractAddress = Addresses.GOVERNOR_ADDRESS
        )
        scenario += minter

        # WHEN setDeveloperFundContract is called by someone other than the governor
        # THEN the request fails
        newDeveloperFundAddress = Addresses.ROTATED_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setDeveloperFundContract(newDeveloperFundAddress).run(
            sender = notGovernor,
            valid = False
        )         
   
    ################################################################
    # setStabilityFee
    ################################################################

    @sp.add_test(name="setStabilityFee - compounds interest")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token
        
        # AND a Minter contract with an interest index
        governorAddress = Addresses.GOVERNOR_ADDRESS
        stabilityFee = 100000000000000000 # 10%
        amountLoaned = Constants.PRECISION * 5 # 5 kUSD
        devFundSplit = sp.nat(100000000000000000) # 10%
        minter = MinterContract(
            governorContractAddress = governorAddress,
            stabilityFee = stabilityFee,
            lastInterestIndexUpdateTime = sp.timestamp(0),
            interestIndex = 1100000000000000000,
            amountLoaned = amountLoaned,
            devFundSplit = devFundSplit,
            tokenContractAddress = token.address,
            developerFundContractAddress = Addresses.DEVELOPER_FUND_ADDRESS,
            stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
        )
        scenario += minter

        # AND the minter is set as the administrator of the token contract
        scenario += token.setAdministrator(minter.address).run(
            sender = governorAddress
        )

        # WHEN setStabilityFee is called by the governor
        newStabilityFee = sp.nat(1)
        now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)    
        scenario += minter.setStabilityFee(newStabilityFee).run(
            sender = governorAddress,
            now = now
        )

        # THEN the the interest is compounded.
        scenario.verify(minter.data.lastInterestIndexUpdateTime == now)
        scenario.verify(minter.data.interestIndex == 1210000000000000000)

        # AND the total borrowed amount was updated
        # expectedAmount = amountLoaned * (1 + (numPeriods * stabilityFee))
        #                = 5 kUSD * (1 + (1 * 0.1))
        #                = 5 kUSD * (1 + 0.1)
        #                = 5 kUSD * 1.1
        #                = 5.5 kUSD
        expectedAmountLoaned = (amountLoaned * (Constants.PRECISION + (1 * stabilityFee))) // Constants.PRECISION
        scenario.verify(expectedAmountLoaned == 5500000000000000000) # 5.5 kUSD
        scenario.verify(minter.data.amountLoaned == expectedAmountLoaned)

        # AND the dev and stability funds received the tokens
        # devFundValue = (newAmountLoaned - oldAmountLoaned) * devFundSplit
        #              = (5.5 - 5) * .1
        #              = .5 * .1
        #              = .05
        # expectedStabilityFundValue = (newAmountLoaned - oldAmountLoaned) - expectedDevFundValue
        #                            = (5.5 - 5) - .05
        #                            = .5 - .05
        #                            = .45
        expectedDevFundValue = (sp.as_nat(expectedAmountLoaned - amountLoaned) * devFundSplit) //Constants.PRECISION
        scenario.verify(expectedDevFundValue == 50000000000000000) # 0.05 kUSD
        scenario.verify(token.data.balances[Addresses.DEVELOPER_FUND_ADDRESS].balance == expectedDevFundValue)

        expectedStabilityFundValue = sp.as_nat(sp.as_nat(expectedAmountLoaned - amountLoaned) - expectedDevFundValue)
        scenario.verify(expectedStabilityFundValue == 450000000000000000) # 0.45 kUSD
        scenario.verify(token.data.balances[Addresses.STABILITY_FUND_ADDRESS].balance == expectedStabilityFundValue)

    @sp.add_test(name="setStabilityFee - updates value")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            stabilityFee = sp.nat(1)
        )
        scenario += minter

        # WHEN setStabilityFee is called by the governor
        newStabilityFee = sp.nat(2)
        scenario += minter.setStabilityFee(newStabilityFee).run(
            sender = governorAddress,
            now = sp.timestamp_from_utc_now(),
        )

        # THEN the parameters are updated.
        scenario.verify(minter.data.stabilityFee == newStabilityFee)

    @sp.add_test(name="setStabilityFee - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            stabilityFee = sp.nat(1),
        )
        scenario += minter

        # WHEN setStabilityFee is called by someone other than the governor THEN the request fails
        newStabilityFee = sp.nat(2)
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setStabilityFee(newStabilityFee).run(
            sender = notGovernor,
            now = sp.timestamp_from_utc_now(),
            valid = False,
        )

    @sp.add_test(name="setStabilityFee - fails if not initialized")
    def test():
        scenario = sp.test_scenario()

        # GVIEN a Minter contract that is uninitialized
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            stabilityFee = sp.nat(1),
            initialized = False,
        )
        scenario += minter

        # WHEN setStabilityFee is called by the governor
        # THEN the call fails with NOT_INITIALIZED
        newStabilityFee = sp.nat(2)
        scenario += minter.setStabilityFee(newStabilityFee).run(
            sender = governorAddress,
            now = sp.timestamp_from_utc_now(),

            valid = False,
            exception = Errors.NOT_INITIALIZED
        )

    ################################################################
    # setLiquidationFeePercent
    ################################################################

    @sp.add_test(name="setLiquidationFeePercent - updates value")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            liquidationFeePercent = sp.nat(1)
        )
        scenario += minter

        # WHEN setLiquidationFeePercent is called by the governor
        newLiquidationFeePercent = sp.nat(2)
        scenario += minter.setLiquidationFeePercent(newLiquidationFeePercent).run(
            sender = governorAddress,
        )

        # THEN the parameters are updated.
        scenario.verify(minter.data.liquidationFeePercent == newLiquidationFeePercent)

    @sp.add_test(name="setLiquidationFeePercent - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            collateralizationPercentage = sp.nat(1)
        )
        scenario += minter

        # WHEN setCollateralizationPercentage is called by someone other than the governor THEN the request fails
        newLiquidationFeePercent = sp.nat(2)
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setLiquidationFeePercent(newLiquidationFeePercent).run(
            sender = notGovernor,
            valid = False
        )        

    ################################################################
    # setCollateralizationPercentage
    ################################################################

    @sp.add_test(name="setCollateralizationPercentage - updates value")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            collateralizationPercentage = sp.nat(1)
        )
        scenario += minter

        # WHEN setCollateralizationPercentage is called by the governor
        newCollateralizationPercentage = sp.nat(2)
        scenario += minter.setCollateralizationPercentage(newCollateralizationPercentage).run(
            sender = governorAddress,
        )

        # THEN the parameters are updated.
        scenario.verify(minter.data.collateralizationPercentage == newCollateralizationPercentage)

    @sp.add_test(name="setCollateralizationPercentage - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            collateralizationPercentage = sp.nat(1)
        )
        scenario += minter

        # WHEN setCollateralizationPercentage is called by someone other than the governor THEN the request fails
        newCollateralizationPercentage = sp.nat(2)
        notGovernor = Addresses.NULL_ADDRESS
        scenario += minter.setCollateralizationPercentage(newCollateralizationPercentage).run(
            sender = notGovernor,
            valid = False
        )        

    ################################################################
    # updateFundSplits
    ################################################################

    @sp.add_test(name="updateFundSplits - updates the fund splits")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract with a devFundSplit
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            devFundSplit = 100000000000000000,
        )
        scenario += minter

        # WHEN updateFundSplits is called by the governor
        newDevFundSplit = 200000000000000000
        newStabilityFundSplit = sp.as_nat(Constants.PRECISION - newDevFundSplit)
        newSplits = sp.record(
            developerFundSplit = newDevFundSplit, 
            stabilityFundSplit = newStabilityFundSplit
        )
        scenario += minter.updateFundSplits(newSplits).run(
            sender = governorAddress,
        )

        # THEN the splits are updated
        scenario.verify(minter.data.devFundSplit == newDevFundSplit)

    @sp.add_test(name="updateFundSplits - fails if splits do not sum to one")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract with a devFundSplit
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            devFundSplit = 100000000000000000,
        )
        scenario += minter

        # WHEN updateFundSplits is called by the governor with splits that do not add to 1.0
        # THEN the update fails
        newDevFundSplit = 200000000000000000
        newStabilityFundSplit = sp.as_nat(Constants.PRECISION - newDevFundSplit - 1)
        newSplits = sp.record(
            developerFundSplit = newDevFundSplit, 
            stabilityFundSplit = newStabilityFundSplit
        )
        scenario += minter.updateFundSplits(newSplits).run(
            sender = governorAddress,
            valid = False
        )

    @sp.add_test(name="updateFundSplits - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract with a devFundSplit
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            devFundSplit = 100000000000000000,
        )
        scenario += minter

        # WHEN updateFundSplits is called by someone other than the governor
        # THEN the call fails
        newDevFundSplit = 200000000000000000
        newStabilityFundSplit = sp.as_nat(Constants.PRECISION - newDevFundSplit)
        newSplits = sp.record(
            developerFundSplit = newDevFundSplit, 
            stabilityFundSplit = newStabilityFundSplit
        )
        scenario += minter.updateFundSplits(newSplits).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )

    ################################################################
    # setPrivateLiquidationThreshold
    ################################################################

    @sp.add_test(name="setPrivateLiquidationThreshold - updates the private liquidation fee percent")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract with a setPrivateLiquidationThreshold
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            privateOwnerLiquidationThreshold = 12345,
        )
        scenario += minter

        # WHEN setPrivateLiquidationThreshold is called by the governor
        newprivateOwnerLiquidationThreshold = 67890
        scenario += minter.setPrivateLiquidationThreshold(newprivateOwnerLiquidationThreshold).run(
            sender = governorAddress,
        )

        # THEN the percent is updated
        scenario.verify(minter.data.privateOwnerLiquidationThreshold == newprivateOwnerLiquidationThreshold)

    @sp.add_test(name="setPrivateLiquidationThreshold - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract with a devFundSplit
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            privateOwnerLiquidationThreshold = 12345,
        )
        scenario += minter

        # WHEN setPrivateLiquidationThreshold is called by someone other than the governor
        # THEN the call fails
        newprivateOwnerLiquidationThreshold = 67890
        scenario += minter.setPrivateLiquidationThreshold(newprivateOwnerLiquidationThreshold).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )

    ################################################################
    # setLiquidityPoolContract
    ################################################################

    @sp.add_test(name="setLiquidityPoolContract - updates liquidity pool")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS
        )
        scenario += minter

        # WHEN setLiquidityPoolContract is called by the governor
        newLiquidityPoolAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setLiquidityPoolContract(newLiquidityPoolAddress).run(
            sender = governorAddress,
        )

        # THEN the governor is updated.
        scenario.verify(minter.data.liquidityPoolContractAddress == newLiquidityPoolAddress)

    @sp.add_test(name="setLiquidityPoolContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Minter contract
        governorAddress = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            governorContractAddress = governorAddress,
            liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS
        )
        scenario += minter

        # WHEN setGovernorContract is called by someone other than the governor
        # THEN the request fails
        notGovernor = Addresses.NULL_ADDRESS
        newLiquidityPoolAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setLiquidityPoolContract(newLiquidityPoolAddress).run(
            sender = notGovernor,
            valid = False
        )
    
    ################################################################
    # initialize
    ################################################################

    @sp.add_test(name="initialize - can initialize the contract")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an unitialized Minter contract
        initializer = Addresses.INITIALIZER_ADDRESS
        minter = MinterContract(
            initializerContractAddress = initializer,
            initialized = False,
            amountLoaned = sp.nat(0)
        )
        scenario += minter

        # WHEN initialize is called
        amountLoaned = sp.nat(123)
        scenario += minter.initialize(amountLoaned).run(
            sender = initializer
        )

        # THEN the contract initializes amountLoaned storage variable
        scenario.verify(minter.data.amountLoaned == amountLoaned)

        # AND the contract is set to be initialized
        scenario.verify(minter.data.initialized == True)

    @sp.add_test(name="initialize - fails to initialize an initialized contract")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an Minter contract that is initialized
        initializer = Addresses.INITIALIZER_ADDRESS
        minter = MinterContract(
            initializerContractAddress = initializer,
            initialized = True,
            amountLoaned = sp.nat(0)
        )
        scenario += minter

        # WHEN initialize is called
        # THEN the call fails with ALREADY_INITIALIZED
        amountLoaned = sp.nat(123)
        scenario += minter.initialize(amountLoaned).run(
            sender = initializer,
            
            valid = False,
            exception = Errors.ALREADY_INITIALIZED
        )

    @sp.add_test(name="initialize - fails if not called by initializer")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an Minter contract
        initializer = Addresses.INITIALIZER_ADDRESS
        minter = MinterContract(
            initializerContractAddress = initializer,
            initialized = False,
            amountLoaned = sp.nat(0)
        )
        scenario += minter

        # WHEN initialize is called by someone other than the initializer address
        # THEN the call fails with BAD_SENDER
        notInitializer = Addresses.NULL_ADDRESS
        amountLoaned = sp.nat(123)
        scenario += minter.initialize(amountLoaned).run(
            sender = notInitializer,
            
            valid = False,
            exception = Errors.BAD_SENDER
        )

    ################################################################
    # setInitializerContract
    ################################################################

    @sp.add_test(name="setInitializerContract - can rotate initializer")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an unitialized Minter contract
        initializer = Addresses.INITIALIZER_ADDRESS
        governor = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            initializerContractAddress = initializer,
            governorContractAddress = governor
        )
        scenario += minter

        # WHEN initialize is called
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setInitializerContract(rotatedAddress).run(
            sender = governor
        )

        # THEN the initializer is updated
        scenario.verify(minter.data.initializerContractAddress == rotatedAddress)

    @sp.add_test(name="setInitializerContract - fails if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an unitialized Minter contract
        initializer = Addresses.INITIALIZER_ADDRESS
        governor = Addresses.GOVERNOR_ADDRESS
        minter = MinterContract(
            initializerContractAddress = initializer,
            governorContractAddress = governor
        )
        scenario += minter

        # WHEN initialize is called by someone other than the governor
        # THEN the call fails with NOT_GOVERNOR
        notGovernor = Addresses.NULL_ADDRESS
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += minter.setInitializerContract(rotatedAddress).run(
            sender = notGovernor,

            valid = False,
            exception = Errors.NOT_GOVERNOR
        )

    ################################################################
    # getStabilityFee
    ################################################################        

    @sp.add_test(name = "getStabilityFee - returns the current stability fee")
    def test():
        scenario = sp.test_scenario()
    
        # GIVEN a minter contract with a stability fee
        stabilityFee = 123
        minter = MinterContract(
            stabilityFee = stabilityFee
        )
        scenario += minter
        
        # WHEN the interest index is retrieved
        # THEN the stability fee is returned
        scenario.verify(minter.getStabilityFee() == stabilityFee)

    ################################################################
    # getStorage
    ################################################################        

    @sp.add_test(name = "getStorage - returns the contracts storage")
    def test():
        scenario = sp.test_scenario()
    
        # GIVEN a minter contract with a stability fee
        stabilityFee = 123
        minter = MinterContract(
            stabilityFee = stabilityFee
        )
        scenario += minter
        
        # WHEN the storage is returned
        # THEN the stability fee exists in it
        scenario.verify(minter.getStorage().stabilityFee == stabilityFee)        

    ################################################################
    # getInterestIndex
    ################################################################        

    # TODO(keefertaylor): Document
    # TODO(keefertaylor): Move to the correct location
    # TODO(keefertaylor): Rename
    class TestOnchainView(sp.Contract):
        def __init__(self, f):
            self.f = sp.build_lambda(f.f)
            self.compoundWithLinearApproximation_implementation = MinterContract.compoundWithLinearApproximation_implementation
            self.init(result = sp.none)

        @sp.entry_point
        def compute(self, data):
            self.data.result = sp.some(self.f(sp.record(data = data)))

        # tester = Tester(minter.compoundWithLinearApproximation)
        # scenario += tester

        # # Two periods back to back
        # scenario += tester.compute(
        #     data = minter.data,
        #     param = (1 * Constants.PRECISION, (100000000000000000, 1))
        # )
        # scenario.verify(tester.data.result.open_some() == sp.nat(1100000000000000000))

    @sp.add_test(name = "getCurrentInterestIndex - returns the correct interest index")
    def test():
        scenario = sp.test_scenario()
    
        # GIVEN a minter contract with a stability fee
        interestIndex = Constants.PRECISION # 1.0
        initialTime = sp.timestamp(0) # The beginning of time
        minter = MinterContract(
            interestIndex = interestIndex,
            stabilityFee = Constants.PRECISION // 10, # 10%
            lastInterestIndexUpdateTime = initialTime, 
        )
        scenario += minter
    
    #     # AND a tester to test the view at different points in time
    #     tester = TestOnchainView(minter.getCurrentInterestIndex)
    #     scenario += tester

    #     # WHEN the tester is run after no interest periods
    #     scenario += tester.computeWithUnitParam(
    #         data = minter.data,
    #     ).run(now = initialTime)

    #     # THEN the original interestIndex is returned
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime)
    #     scenario.verify(tester.data.result == sp.some(interestIndex))

    #     # WHEN the tester is run after one interest period
    #     # THEN the original interestIndex is linearly approximated for one period
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + Constants.SECONDS_PER_COMPOUND)
    #     scenario.verify(tester.data.result == sp.some(1100000000000000000))

    #     # WHEN the tester is run after two interest periods
    #     # THEN the original interestIndex is linearly approximated for two periods
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + (2 * Constants.SECONDS_PER_COMPOUND))
    #     scenario.verify(tester.data.result == sp.some(1200000000000000000))

    # @sp.add_test(name = "getAmountLoaned - returns the correct interest index after 0 periods")
    # def test():
    #     scenario = sp.test_scenario()
    
    #     # GIVEN a minter contract with a stability fee
    #     amountLoaned = Constants.PRECISION # 1 kUSD
    #     initialTime = sp.timestamp(0) # The beginning of time
    #     minter = MinterContract(
    #         amountLoaned = amountLoaned,
    #         stabilityFee = Constants.PRECISION // 10, # 10%
    #         lastInterestIndexUpdateTime = initialTime, 
    #     )
    #     scenario += minter

    #     # AND a tester to test the view at different points in time
    #     tester = TestOnchainView(minter.getAmountLoaned, minter)
    #     scenario.register(tester)
    #     onchainViewTester.compute(data = minter.data, params = 42).run(now = sp.timestamp(1))

    #     # WHEN the tester is run after no interest periods
    #     # THEN the original amountLoaned is returned
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime)
    #     scenario.verify(tester.data.result == sp.some(amountLoaned))

    #     # WHEN the tester is run after one interest period
    #     # THEN the original amountLoaned is linearly approximated for one period
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + Constants.SECONDS_PER_COMPOUND)
    #     scenario.verify(tester.data.result == sp.some(1100000000000000000))

    #     # WHEN the tester is run after two interest periods
    #     # THEN the original amountLoaned is linearly approximated for two periods
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + (2 * Constants.SECONDS_PER_COMPOUND))
    #     scenario.verify(tester.data.result == sp.some(1200000000000000000))

    # @sp.add_test(name = "getOvenLoanAmount - returns the correct amount loaned from an oven")
    # def test():
    #     scenario = sp.test_scenario()
    
    #     # GIVEN a minter contract with a stability fee
    #     initialInterestIndex = Constants.PRECISION # 1.0
    #     initialTime = sp.timestamp(0) # The beginning of time
    #     minter = MinterContract(
    #         stabilityFee = Constants.PRECISION // 10, # 10%
    #         lastInterestIndexUpdateTime = initialTime, 
    #         interestIndex = initialInterestIndex
    #     )
    #     scenario += minter

    #     # AND some parameters for an oven
    #     ovenBorrowedTokens = 7 * Constants.PRECISION # 7 kUSD
    #     ovenStabilityFeeTokens = sp.to_int(3 * Constants.PRECISION) # 3 kUSD
    #     ovenInterestIndex = sp.to_int(initialInterestIndex)

    #     # AND a tester to test the view at different points in time
    #     tester = TestOnchainView(minter.getOvenLoanAmount, minter)
    #     scenario.register(tester)
    #     onchainViewTester.compute(data = minter.data, params = 42).run(now = sp.timestamp(1))

    #     # WHEN the tester is run after no interest periods
    #     # THEN the original amountLoaned is returned
    #     param = sp.record(
    #         ovenBorrowedTokens = ovenBorrowedTokens,
    #         ovenStabilityFeeTokens = ovenStabilityFeeTokens,
    #         ovenInterestIndex = ovenInterestIndex
    #     )
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime)
    #     scenario.verify(tester.data.result == sp.some(10 * Constants.PRECISION)) # 10 kUSD - the original amount

    #     # WHEN the tester is run after one interest period
    #     # THEN the original amountLoaned is linearly approximated for one period
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + Constants.SECONDS_PER_COMPOUND)
    #     scenario.verify(tester.data.result == sp.some(11000000000000000000)) # 11 kUSD

    #     # WHEN the tester is run after two interest periods
    #     # THEN the original amountLoaned is linearly approximated for two periods
    #     scenario += tester.compute(minter.data, sp.unit).run(now = initialTime + (2 * Constants.SECONDS_PER_COMPOUND))
    #     scenario.verify(tester.data.result == sp.some(12000000000000000000)) # 12 kUSD     

    sp.add_compilation_target("minter", MinterContract())
