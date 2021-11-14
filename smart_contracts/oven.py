import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")
OvenApi = sp.io.import_script_from_url("file:common/oven-api.py")

################################################################
# Contract
################################################################

class OvenContract(sp.Contract):
    # Initialize a new Oven.
    #
    # Parameters:
    #   owner: The owner of the oven.
    def __init__(
        self, 
        owner = Addresses.OVEN_OWNER_ADDRESS,
        borrowedTokens = sp.nat(0),
        stabilityFeeTokens = sp.int(0),
        interestIndex = sp.to_int(Constants.PRECISION),
        isLiquidated = False,
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContractAddress
        )

    ################################################################
    # Public API
    ################################################################

    @sp.entry_point
    def borrow(self, tokensToBorrow):
        sp.set_type(tokensToBorrow, sp.TNat)

        # Verify the caller is the owner.
        sp.verify(sp.sender == self.data.owner, message = Errors.NOT_OWNER)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Convert mutez to 10^-18 scale.
        normalizedBalance = sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

        # Call minter.
        minterParam = (sp.to_address(sp.self), (self.data.owner, (normalizedBalance, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, tokensToBorrow)))))))
        minterHandle = sp.contract(
            OvenApi.BORROW_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.BORROW_ENTRY_POINT_NAME,
        ).open_some()
        sp.transfer(minterParam, sp.balance, minterHandle)

    @sp.entry_point
    def repay(self, tokensToRepay):
        sp.set_type(tokensToRepay, sp.TNat)

        # Verify the caller is the owner.
        sp.verify(sp.sender == self.data.owner, message = Errors.NOT_OWNER)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Convert mutez to 10^-18 scale.
        normalizedBalance = sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

        # Call minter.
        minterParam = (sp.to_address(sp.self), (self.data.owner, (normalizedBalance, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, tokensToRepay)))))))
        minterHandle = sp.contract(
            OvenApi.REPAY_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.REPAY_ENTRY_POINT_NAME,
        ).open_some()
        sp.transfer(minterParam, sp.balance, minterHandle)
    
    @sp.entry_point
    def withdraw(self, mutezToWithdraw):
        sp.set_type(mutezToWithdraw, sp.TMutez)

        # Verify the caller is the owner.
        sp.verify(sp.sender == self.data.owner, message = Errors.NOT_OWNER)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Convert mutez to 10^-18 scale.
        normalizedBalance = sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

        # Call minter.
        minterParam = (sp.to_address(sp.self), (self.data.owner, (normalizedBalance, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, mutezToWithdraw)))))))
        minterHandle = sp.contract(
            OvenApi.WITHDRAW_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.WITHDRAW_ENTRY_POINT_NAME,
        ).open_some()
        sp.transfer(minterParam, sp.balance, minterHandle)

    # Note this entrypoint is the 'default' point, but semantically it represents the 'deposit' function.
    @sp.entry_point
    def default(self, unit):
        sp.set_type(unit, sp.TUnit)

        # Convert mutez to 10^-18 scale.
        normalizedBalance = sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

        # Call minter. Send along the new deposit, and the old deposits.
        minterAmount = sp.balance
        minterParam = (sp.to_address(sp.self), (self.data.owner, (normalizedBalance, (self.data.borrowedTokens, (self.data.isLiquidated, (self.data.stabilityFeeTokens, self.data.interestIndex))))))
        minterHandle = sp.contract(
            OvenApi.DEPOSIT_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.DEPOSIT_ENTRY_POINT_NAME,
        ).open_some()        
        sp.transfer(minterParam, minterAmount, minterHandle)

    @sp.entry_point
    def liquidate(self, unit):
        sp.set_type(unit, sp.TUnit)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Convert mutez to 10^-18 scale.
        normalizedBalance = sp.fst(sp.ediv(sp.balance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

        # Call minter.
        minterParam = (sp.to_address(sp.self), (self.data.owner, (normalizedBalance, (self.data.borrowedTokens, ((self.data.isLiquidated, (self.data.stabilityFeeTokens, (self.data.interestIndex, sp.sender))))))))
        minterHandle = sp.contract(
            OvenApi.LIQUIDATE_PARAMETER_TYPE,
            self.data.ovenProxyContractAddress,
            OvenApi.LIQUIDATE_ENTRY_POINT_NAME,
        ).open_some()
        sp.transfer(minterParam, sp.balance, minterHandle)
    
    @sp.entry_point
    def setDelegate(self, newDelegate):
        sp.set_type(newDelegate, sp.TOption(sp.TKeyHash))

        # Verify the caller is the owner.
        sp.verify(sp.sender == self.data.owner, message = Errors.NOT_OWNER)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        sp.set_delegate(newDelegate)

    ################################################################
    # Minter Interface
    ################################################################

    @sp.entry_point
    def updateState(self, param):
        sp.set_type(param, OvenApi.UPDATE_STATE_PARAMETER_TYPE)

        # Verify input came from Minter and was addressed correctly.
        sp.verify(sp.sender == self.data.ovenProxyContractAddress, message = Errors.NOT_OVEN_PROXY)
        sp.verify(sp.fst(param) == sp.to_address(sp.self), message = Errors.BAD_DESTINATION)

        self.data.borrowedTokens     =  sp.fst(sp.snd(param))
        self.data.stabilityFeeTokens =  sp.fst(sp.snd(sp.snd(param)))
        self.data.interestIndex      =  sp.fst(sp.snd(sp.snd(sp.snd(param))))
        self.data.isLiquidated       =  sp.snd(sp.snd(sp.snd(sp.snd(param))))

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    MockOvenProxy = sp.io.import_script_from_url("file:test-helpers/mock-oven-proxy.py")

    ################################################################
    # Borrow
    ################################################################

    @sp.add_test(name="borrow - fails with bad owner")
    def test():
        # GIVEN a oven contract with an owner.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN borrow is called by someone other than the owner THEN the invocation fails.
        notOwner = Addresses.NULL_ADDRESS
        scenario += contract.borrow(1).run(
            sender = notOwner,
            valid = False
        )

    @sp.add_test(name="borrow - fails with amount")
    def test():
        # GIVEN a oven contract.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN borrow is called with an amount of mutez THEN the invocation fails.
        scenario += contract.borrow(1).run(
            sender = owner,
            amount = sp.mutez(1),
            valid = False
        )    

    @sp.add_test(name="borrow - calls oven proxy successfully")
    def test():
        # GIVEN a oven contract, a mock oven proxy, and some parameters set in the oven.
        scenario = sp.test_scenario()

        borrowedTokens = 1
        stabilityFeeTokens = 2
        interestIndex = 3
        isLiquidated = True
        owner = Addresses.OVEN_OWNER_ADDRESS
        contractBalance = sp.mutez(4)

        ovenProxyContract = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxyContract

        contract = OvenContract(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContract.address
        )
        contract.set_initial_balance(contractBalance)
        scenario += contract

        # WHEN borrow is called
        tokensToBorrow = sp.nat(5)
        scenario += contract.borrow(tokensToBorrow).run(
            sender = owner,
        )    

        # THEN the parameters were passed to the minter correctly. 
        expectedBalance = sp.fst(sp.ediv(contractBalance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(ovenProxyContract.data.borrow_ovenAddress == contract.address)
        scenario.verify(ovenProxyContract.data.borrow_ownerAddress == owner)
        scenario.verify(ovenProxyContract.data.borrow_ovenBalance == expectedBalance)
        scenario.verify(ovenProxyContract.data.borrow_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxyContract.data.borrow_liquidated == isLiquidated)
        scenario.verify(ovenProxyContract.data.borrow_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(ovenProxyContract.data.borrow_ovenInterestIndex == interestIndex)
        scenario.verify(ovenProxyContract.data.borrow_tokensToBorrow == tokensToBorrow)
        
        # AND the minter has the balance of the oven.
        scenario.verify(ovenProxyContract.balance == contractBalance)

    ################################################################
    # Repay
    ################################################################

    @sp.add_test(name="repay - fails with bad owner")
    def test():
        # GIVEN a oven contract with an owner.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN repay is called by someone other than the owner THEN the invocation fails.
        notOwner = Addresses.NULL_ADDRESS
        scenario += contract.repay(1).run(
            sender = notOwner,
            valid = False
        )

    @sp.add_test(name="repay - fails with amount")
    def test():
        # GIVEN a oven contract.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN repay is called with an amount THEN the invocation fails.
        scenario += contract.repay(1).run(
            sender = owner,
            amount = sp.mutez(1),
            valid = False
        )    

    @sp.add_test(name="repay - calls oven proxy successfully")
    def test():
        # GIVEN a oven contract, a mock oven proxy, and some parameters set in the oven.
        scenario = sp.test_scenario()

        borrowedTokens = 1
        stabilityFeeTokens = 2
        interestIndex = 3
        isLiquidated = True
        owner = Addresses.OVEN_OWNER_ADDRESS
        contractBalance = sp.mutez(4)

        ovenProxyContract = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxyContract

        contract = OvenContract(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContract.address
        )
        contract.set_initial_balance(contractBalance)
        scenario += contract

        # WHEN repay is called
        tokensToRepay = sp.nat(5)
        scenario += contract.repay(tokensToRepay).run(
            sender = owner,
        )    

        # THEN the parameters were passed to the minter correctly. 
        expectedBalance = sp.fst(sp.ediv(contractBalance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(ovenProxyContract.data.repay_ovenAddress == contract.address)
        scenario.verify(ovenProxyContract.data.repay_ownerAddress == owner)
        scenario.verify(ovenProxyContract.data.repay_ovenBalance == expectedBalance)
        scenario.verify(ovenProxyContract.data.repay_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxyContract.data.repay_liquidated == isLiquidated)
        scenario.verify(ovenProxyContract.data.repay_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(ovenProxyContract.data.repay_ovenInterestIndex == interestIndex)
        scenario.verify(ovenProxyContract.data.repay_tokensToRepay == tokensToRepay)
        
        # AND the minter has the balance of the oven.
        scenario.verify(ovenProxyContract.balance == contractBalance)

    ################################################################
    # Default (Deposit)
    ################################################################
    
    @sp.add_test(name="default - calls oven proxy successfully")
    def test():
        # GIVEN a oven contract, a mock oven proxy, and some parameters set in the oven.
        scenario = sp.test_scenario()

        borrowedTokens = 1
        stabilityFeeTokens = 2
        interestIndex = 3
        isLiquidated = True
        owner = Addresses.OVEN_OWNER_ADDRESS
        contractBalance = sp.mutez(4)

        ovenProxyContract = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxyContract

        contract = OvenContract(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContract.address
        )
        contract.set_initial_balance(contractBalance)
        scenario += contract

        # WHEN the default (deposit) entrypoint is called
        amountToDeposit = sp.mutez(5)
        scenario += contract.default(sp.unit).run(
            sender = owner,
            amount = amountToDeposit
        )    

        # THEN the parameters were passed to the minter correctly. 
        expectedBalance = sp.fst(sp.ediv((contractBalance + amountToDeposit), sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(ovenProxyContract.data.deposit_ovenAddress == contract.address)
        scenario.verify(ovenProxyContract.data.deposit_ownerAddress == owner)
        scenario.verify(ovenProxyContract.data.deposit_ovenBalance == expectedBalance)
        scenario.verify(ovenProxyContract.data.deposit_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxyContract.data.deposit_liquidated == isLiquidated)
        scenario.verify(ovenProxyContract.data.deposit_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(ovenProxyContract.data.deposit_ovenInterestIndex == interestIndex)
        
        # AND the minter has the balance of the oven.
        scenario.verify(ovenProxyContract.balance == (contractBalance + amountToDeposit))

    ################################################################
    # Withdraw
    ################################################################

    @sp.add_test(name="withdraw - fails with bad owner")
    def test():
        # GIVEN a oven contract with an owner.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN withdraw is called by someone other than the owner THEN the invocation fails.
        notOwner = Addresses.NULL_ADDRESS
        scenario += contract.withdraw(sp.mutez(1)).run(
            sender = notOwner,
            valid = False
        )

    @sp.add_test(name="withdraw - fails with an amount")
    def test():
        # GIVEN a oven contract.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN withdraw is called with an amount THEN the invocation fails.
        scenario += contract.withdraw(sp.mutez(1)).run(
            sender = owner,
            amount = sp.mutez(1),
            valid = False
        )


    @sp.add_test(name="withdraw - calls oven proxy successfully")
    def test():
        # GIVEN a oven contract, a mock oven proxy, and some parameters set in the oven.
        scenario = sp.test_scenario()

        borrowedTokens = 1
        stabilityFeeTokens = 2
        interestIndex = 3
        isLiquidated = True
        owner = Addresses.OVEN_OWNER_ADDRESS
        contractBalance = sp.mutez(4)

        ovenProxyContract = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxyContract

        contract = OvenContract(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContract.address
        )
        contract.set_initial_balance(contractBalance)
        scenario += contract

        # WHEN withdraw is called
        mutezToWithdraw = sp.mutez(5)
        scenario += contract.withdraw(mutezToWithdraw).run(
            sender = owner,
        )    

        # THEN the parameters were passed to the minter correctly. 
        expectedBalance = sp.fst(sp.ediv(contractBalance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(ovenProxyContract.data.withdraw_ovenAddress == contract.address)
        scenario.verify(ovenProxyContract.data.withdraw_ownerAddress == owner)
        scenario.verify(ovenProxyContract.data.withdraw_ovenBalance == expectedBalance)
        scenario.verify(ovenProxyContract.data.withdraw_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxyContract.data.withdraw_liquidated == isLiquidated)
        scenario.verify(ovenProxyContract.data.withdraw_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(ovenProxyContract.data.withdraw_ovenInterestIndex == interestIndex)
        scenario.verify(ovenProxyContract.data.withdraw_mutezToWithdraw == mutezToWithdraw)
        
        # AND the minter has the balance of the oven.
        scenario.verify(ovenProxyContract.balance == contractBalance)

    ################################################################
    # Liquidate
    ################################################################

    @sp.add_test(name="liquidate - fails with an amount")
    def test():
        # GIVEN a oven contract.
        scenario = sp.test_scenario()

        contract = OvenContract()
        scenario += contract

        # WHEN liquidate is called with an amount THEN the invocation fails.
        scenario += contract.withdraw(sp.mutez(1)).run(
            amount = sp.mutez(1),
            valid = False
        )

    @sp.add_test(name="liquidate - calls oven proxy successfully")
    def test():
        # GIVEN a oven contract, a mock oven proxy, and some parameters set in the oven.
        scenario = sp.test_scenario()

        borrowedTokens = 1
        stabilityFeeTokens = 2
        interestIndex = 3
        isLiquidated = True
        owner = Addresses.OVEN_OWNER_ADDRESS
        contractBalance = sp.mutez(4)

        ovenProxyContract = MockOvenProxy.MockOvenProxyContract()
        scenario += ovenProxyContract

        contract = OvenContract(
            owner = owner,
            borrowedTokens = borrowedTokens,
            stabilityFeeTokens = stabilityFeeTokens,
            interestIndex = interestIndex,
            isLiquidated = isLiquidated,
            ovenProxyContractAddress = ovenProxyContract.address
        )
        contract.set_initial_balance(contractBalance)
        scenario += contract

        # WHEN liquidate is called
        liquidatorAddress = Addresses.LIQUIDATOR_ADDRESS
        scenario += contract.liquidate(sp.unit).run(
            sender = liquidatorAddress,
        )    

        # THEN the parameters were passed to the minter correctly. 
        expectedBalance = sp.fst(sp.ediv(contractBalance, sp.mutez(1)).open_some()) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(ovenProxyContract.data.liquidate_ovenAddress == contract.address)
        scenario.verify(ovenProxyContract.data.liquidate_ownerAddress == owner)
        scenario.verify(ovenProxyContract.data.liquidate_ovenBalance == expectedBalance)
        scenario.verify(ovenProxyContract.data.liquidate_borrowedTokens == borrowedTokens)
        scenario.verify(ovenProxyContract.data.liquidate_liquidated == isLiquidated)
        scenario.verify(ovenProxyContract.data.liquidate_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(ovenProxyContract.data.liquidate_ovenInterestIndex == interestIndex)
        scenario.verify(ovenProxyContract.data.liquidate_liquidatorAddress == liquidatorAddress)
        
        # AND the minter has the balance of the oven.
        scenario.verify(ovenProxyContract.balance == contractBalance)

    ################################################################
    # Set Delegate
    ################################################################

    @sp.add_test(name="setDelegate - fails with bad owner")
    def test():
        # GIVEN a oven contract without a delegate and an owner.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN setDelegate is called by someone other than the owner THEN the invocation fails.
        notOwner = Addresses.NULL_ADDRESS
        delegate = sp.some(sp.key_hash("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"))
        scenario += contract.setDelegate(delegate).run(
            sender = notOwner,
            valid = False
        )

    @sp.add_test(name="setDelegate - updates delegate")
    def test():
        # GIVEN a oven contract without a delegate and an owner.
        scenario = sp.test_scenario()
        owner = Addresses.OVEN_OWNER_ADDRESS

        contract = OvenContract(
            owner = owner
        )
        scenario += contract

        # WHEN setDelegate is called by the owner
        delegate = sp.some(sp.key_hash("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"))
        scenario += contract.setDelegate(delegate).run(
            sender = owner,
        )

        # THEN the delegate is updated.
        scenario.verify(contract.baker.open_some() == delegate.open_some())

    ################################################################
    # Update State
    ################################################################

    @sp.add_test(name="updateState - fails when sender is not OvenProxy")
    def test():
        # GIVEN a oven contract with an oven contract proxy.
        scenario = sp.test_scenario()
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS

        contract = OvenContract(
            ovenProxyContractAddress = ovenProxyContractAddress
        )
        scenario += contract

        # WHEN updateState is called by someone other than the OvenProxy THEN the invocation fails.
        notOvenProxy = Addresses.NULL_ADDRESS
        update = (contract.address, (12, (13, (14, False))))
        scenario += contract.updateState(update).run(
            sender = notOvenProxy,
            valid = False
        )

    @sp.add_test(name="updateState - fails when addressee is not oven")
    def test():
        # GIVEN a oven contract with an oven contract proxy.
        scenario = sp.test_scenario()
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS

        contract = OvenContract(
            ovenProxyContractAddress = ovenProxyContractAddress
        )
        scenario += contract

        # WHEN updateState is called with an address that is not the Oven THEN the invocation fails.
        update = (ovenProxyContractAddress, (12, (13, (14, False))))
        scenario += contract.updateState(update).run(
            sender = ovenProxyContractAddress,
            valid = False
        )

    @sp.add_test(name="updateState - successfully updates state")
    def test():
        # GIVEN a oven contract with an oven contract proxy.
        scenario = sp.test_scenario()
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS

        contract = OvenContract(
            ovenProxyContractAddress = ovenProxyContractAddress
        )
        scenario += contract

        # WHEN updateState is called by the OvenProxy
        borrowedTokens = sp.nat(12)
        stabilityFeeTokens = sp.int(13)
        interestIndex = sp.int(14)
        isLiquidated = sp.bool(True)
        update = (contract.address, (borrowedTokens, (stabilityFeeTokens, (interestIndex, isLiquidated))))
        scenario += contract.updateState(update).run(
            sender = ovenProxyContractAddress,
        )    

        # THEN the values are updated.
        scenario.verify(contract.data.borrowedTokens == borrowedTokens)
        scenario.verify(contract.data.stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(contract.data.interestIndex == interestIndex)
        scenario.verify(contract.data.isLiquidated == isLiquidated)

    sp.add_compilation_target("oven", OvenContract())
