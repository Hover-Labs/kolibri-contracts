import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")
OvenApi = sp.io.import_script_from_url("file:common/oven-api.py")

################################################################
# State Machine States.
################################################################

IDLE = 0
BORROW_WAITING_FOR_ORACLE = 1
WITHDRAW_WAITING_FOR_ORACLE = 2
LIQUIDATE_WAITING_FOR_ORACLE = 3

################################################################
# Contract
################################################################

class OvenProxyContract(sp.Contract):
    def __init__(
        self, 
        minterContractAddress = Addresses.MINTER_ADDRESS,
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,
        ovenRegistryContractAddress = Addresses.OVEN_REGISTRY_ADDRESS,
        pauseGuardianContractAddress = Addresses.PAUSE_GUARDIAN_ADDRESS,
        oracleContractAddress = Addresses.ORACLE_ADDRESS,
        paused = False,    
        state = IDLE
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            # Contract Addresses
            minterContractAddress = minterContractAddress,
            governorContractAddress = governorContractAddress,
            ovenRegistryContractAddress = ovenRegistryContractAddress,
            pauseGuardianContractAddress = pauseGuardianContractAddress,
            oracleContractAddress = oracleContractAddress,

            # Pause Guardian
            paused = paused,

            # State and registers
            state = state,
            borrowParams = sp.none,
            withdrawParams = sp.none,
            liquidateParams = sp.none
        )

    ################################################################
    # Public Interface
    ################################################################

    # Disallow direct transfers.
    @sp.entry_point
    def default(self, param):
        sp.set_type(param, sp.TUnit)
        sp.failwith(Errors.CANNOT_RECEIVE_FUNDS)        

    ################################################################
    # Oven Interface
    ################################################################

    @sp.entry_point
    def borrow(self, param):
        sp.set_type(param, OvenApi.BORROW_PARAMETER_TYPE)

        self.verifyIsOven(sp.sender)

        # Verify system is not paused.
        sp.verify(self.data.paused == False, message = Errors.PAUSED)

        # Verify in idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Update state and save params
        self.data.state = BORROW_WAITING_FOR_ORACLE
        self.data.borrowParams = sp.some(param)

        self.callOracleWithCallback('borrow_callback')

    @sp.entry_point
    def borrow_callback(self, oracleResult): 
        sp.set_type(oracleResult, sp.TNat)

        # Verify sender is the oracle
        sp.verify(sp.sender == self.data.oracleContractAddress, message = Errors.NOT_ORACLE)

        # Verify state
        sp.verify(self.data.state == BORROW_WAITING_FOR_ORACLE, message = Errors.BAD_STATE)

        # Load borrow params
        param = (oracleResult, self.data.borrowParams.open_some())
        minterContractHandle = sp.contract(
            OvenApi.BORROW_PARAMETER_TYPE_ORACLE,
            self.data.minterContractAddress,
            OvenApi.BORROW_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.balance, minterContractHandle)

        # Reset state
        self.data.state = IDLE
        self.data.borrowParams = sp.none

    @sp.entry_point
    def repay(self, param):
        sp.set_type(param,  OvenApi.REPAY_PARAMETER_TYPE)

        self.verifyIsOven(sp.sender)

        # Verify system is not paused.
        sp.verify(self.data.paused == False, message = Errors.PAUSED)

        # Verify in idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        minterContractHandle = sp.contract(
            OvenApi.REPAY_PARAMETER_TYPE,
            self.data.minterContractAddress,
            OvenApi.REPAY_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.amount, minterContractHandle)

    @sp.entry_point
    def liquidate(self, param):
        sp.set_type(param, OvenApi.LIQUIDATE_PARAMETER_TYPE)
        self.verifyIsOven(sp.sender)

        # Verify system is not paused.
        sp.verify(self.data.paused == False, message = Errors.PAUSED)

        # Verify in idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Update state and save params
        self.data.state = LIQUIDATE_WAITING_FOR_ORACLE
        self.data.liquidateParams = sp.some(param)

        self.callOracleWithCallback('liquidate_callback')

    @sp.entry_point
    def liquidate_callback(self, oracleResult): 
        sp.set_type(oracleResult, sp.TNat)

        # Verify sender is the oracle
        sp.verify(sp.sender == self.data.oracleContractAddress, message = Errors.NOT_ORACLE)

        # Verify state
        sp.verify(self.data.state == LIQUIDATE_WAITING_FOR_ORACLE, message = Errors.BAD_STATE)

        # Load liquidate params
        param = (oracleResult, self.data.liquidateParams.open_some())
        minterContractHandle = sp.contract(
            OvenApi.LIQUIDATE_PARAMETER_TYPE_ORACLE,
            self.data.minterContractAddress,
            OvenApi.LIQUIDATE_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.balance, minterContractHandle)

        # Reset state
        self.data.state = IDLE
        self.data.liquidateParams = sp.none

    @sp.entry_point
    def withdraw(self, param):
        sp.set_type(param, OvenApi.WITHDRAW_PARAMETER_TYPE)
        self.verifyIsOven(sp.sender)

        # Verify in idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Verify system is not paused.
        sp.verify(self.data.paused == False, message = Errors.PAUSED)

        # Update state and save params
        self.data.state = WITHDRAW_WAITING_FOR_ORACLE
        self.data.withdrawParams = sp.some(param)

        self.callOracleWithCallback('withdraw_callback')

    @sp.entry_point
    def withdraw_callback(self, oracleResult): 
        sp.set_type(oracleResult, sp.TNat)

        # Verify sender is the oracle
        sp.verify(sp.sender == self.data.oracleContractAddress, message = Errors.NOT_ORACLE)

        # Verify state
        sp.verify(self.data.state == WITHDRAW_WAITING_FOR_ORACLE, message = Errors.BAD_STATE)

        # Load withdraw params
        param = (oracleResult, self.data.withdrawParams.open_some())
        minterContractHandle = sp.contract(
            OvenApi.WITHDRAW_PARAMETER_TYPE_ORACLE,
            self.data.minterContractAddress,
            OvenApi.WITHDRAW_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.balance, minterContractHandle)

        # Reset state
        self.data.state = IDLE
        self.data.withdrawParams = sp.none

    @sp.entry_point
    def deposit(self, param):
        sp.set_type(param, OvenApi.DEPOSIT_PARAMETER_TYPE)
        self.verifyIsOven(sp.sender)

        # Verify system is not paused.
        sp.verify(self.data.paused == False, message = Errors.PAUSED)

        # Verify in idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        minterContractHandle = sp.contract(
            OvenApi.DEPOSIT_PARAMETER_TYPE,
            self.data.minterContractAddress,
            OvenApi.DEPOSIT_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.amount, minterContractHandle)

    ################################################################
    # Minter Interface
    ################################################################

    @sp.entry_point
    def updateState(self, param):
        sp.set_type(param, OvenApi.UPDATE_STATE_PARAMETER_TYPE)

        # Verify input came from Minter and was addressed correctly.
        sp.verify(sp.sender == self.data.minterContractAddress, message = Errors.NOT_MINTER)

        # Forward call to destination.
        destination = sp.fst(param)
        ovenHandle = sp.contract(
            OvenApi.UPDATE_STATE_PARAMETER_TYPE,
            destination,
            OvenApi.UPDATE_STATE_ENTRY_POINT_NAME
        ).open_some()
        sp.transfer(param, sp.amount, ovenHandle)

    ################################################################
    # Pause Guardian
    ################################################################

    # Pause the system
    @sp.entry_point
    def pause(self):
        sp.verify(sp.sender == self.data.pauseGuardianContractAddress, message = Errors.NOT_PAUSE_GUARDIAN)
        self.data.paused = True

    ################################################################
    # Governance
    ################################################################

    # Unpause the system.
    @sp.entry_point
    def unpause(self):
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.paused = False

    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # Update the minter contract address.
    @sp.entry_point
    def setMinterContract(self, newMinterContractAddress):
        sp.set_type(newMinterContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.minterContractAddress = newMinterContractAddress

    # Update the oven registry contract address.
    @sp.entry_point
    def setOvenRegistryContract(self, newOvenRegistryContractAddress):
        sp.set_type(newOvenRegistryContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenRegistryContractAddress = newOvenRegistryContractAddress

    # Update the oracle contract address.
    @sp.entry_point
    def setOracleContract(self, newOracleContractAddress):
        sp.set_type(newOracleContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.oracleContractAddress = newOracleContractAddress        

    # Update the pause guardian contract address.
    @sp.entry_point
    def setPauseGuardianContract(self, newPauseGuardianContract):
        sp.set_type(newPauseGuardianContract, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.pauseGuardianContractAddress = newPauseGuardianContract        

    ################################################################
    # Helpers
    ################################################################

    # Check if the given address is a known Oven.
    def verifyIsOven(self, ovenAddress):
        # Make a call to the oven registry.
        contractHandle = sp.contract(
            sp.TAddress,
            self.data.ovenRegistryContractAddress,
            "isOven"
        ).open_some()
        sp.transfer(ovenAddress, sp.mutez(0), contractHandle)

    def callOracleWithCallback(self, entrypoint):
        # Call oracle
        oracleCallback = sp.self_entry_point(entry_point = entrypoint)
        oracleContractHandle = sp.contract(
            sp.TContract(sp.TNat),
            self.data.oracleContractAddress,
            'getXtzUsdRate'
        ).open_some()

        sp.transfer(oracleCallback, sp.mutez(0), oracleContractHandle)

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    MockMinter = sp.io.import_script_from_url("file:test-helpers/mock-minter.py")
    Oven = sp.io.import_script_from_url("file:oven.py")
    Oracle = sp.io.import_script_from_url("file:oracle.py")
    OvenRegistry = sp.io.import_script_from_url("file:oven-registry.py")
    FakeHarbinger = sp.io.import_script_from_url("file:test-helpers/fake-harbinger.py")

    ################################################################
    # withdraw
    ################################################################

    # TODO(keefertaylor): Enable when SmartPy supports handling `failwith` in other contracts with `valid = False`
    # SEE: https://t.me/SmartPy_io/6538@
    # sp.add_test(name="withdraw - fails when not called from oven")
    # def test():
    #     scenario = sp.test_scenario()

    #     # AND a faked Oracle contract
    #     fakeHarbingerValue = sp.nat(8)
    #     harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
    #     scenario += harbinger
    #     oracle = Oracle.OracleContract(
    #         harbingerContractAddress = harbinger.address
    #     )
    #     scenario += oracle

    #     # GIVEN an OvenRegistry contract
    #     ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
    #     ovenRegistry = OvenRegistry.OvenRegistryContract(
    #         ovenFactoryContractAddress = ovenFactoryAddress
    #     )
    #     scenario += ovenRegistry

    #     # AND an oven which is registered
    #     ovenAddress = Addresses.OVEN_ADDRESS
    #     scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
    #         sender = ovenFactoryAddress
    #     )

    #     # AND a mock minter contract
    #     minter = MockMinter.MockMinterContract()
    #     scenario += minter

    #     # AND an OvenProxy
    #     ovenProxy = OvenProxyContract(
    #         ovenRegistryContractAddress = ovenRegistry.address,
    #         minterContractAddress = minter.address,
    #         oracleContractAddress = oracle.address
    #     )
    #     scenario += ovenProxy


    #     scenario += ovenRegistry.isOven(ovenAddress)
    #     scenario += ovenRegistry.isOven(ovenFactoryAddress).run(
    #         valid = False
    #     )

    #     # WHEN withdraw is called by someone other than an oven THEN the call fails.
    #     ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
    #     ovenBalance = sp.nat(1)
    #     borrowedTokens = sp.nat(2)
    #     isLiquidated = False
    #     stabilityFeeTokens = sp.int(3)
    #     interestIndex = sp.int(4)
    #     mutezToWithdraw = sp.mutez(5)
    #     param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, mutezToWithdraw)))))))
    #     amount = sp.mutez(1)
    #     scenario += ovenProxy.withdraw(param).run(
    #         sender = ovenFactoryAddress,
    #         amount = amount,
    #         valid = False
    #     )   

    @sp.add_test(name="withdraw - fails when paused")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy which is paused
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN withdraw is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        mutezToWithdraw = sp.mutez(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, mutezToWithdraw)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.withdraw(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="withdraw - fails when in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE_STATE state
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN withdraw is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        mutezToWithdraw = sp.mutez(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, mutezToWithdraw)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.withdraw(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="withdraw - passes withdraw params")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address
        )
        scenario += ovenProxy

        # WHEN withdraw is called by an oven
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        mutezToWithdraw = sp.mutez(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, mutezToWithdraw)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.withdraw(param).run(
            sender = ovenAddress,
            amount = amount,
            now = sp.timestamp_from_utc_now()
        )   

        # THEN the minter contract receives the parameters
        scenario.verify(minter.data.withdraw_ovenAddress == ovenAddress)
        scenario.verify(minter.data.withdraw_ownerAddress == ownerAddress)
        scenario.verify(minter.data.withdraw_ovenBalance == ovenBalance)
        scenario.verify(minter.data.withdraw_borrowedTokens == borrowedTokens)
        scenario.verify(minter.data.withdraw_liquidated == isLiquidated)
        scenario.verify(minter.data.withdraw_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(minter.data.withdraw_ovenInterestIndex == interestIndex)
        scenario.verify(minter.data.withdraw_mutezToWithdraw == mutezToWithdraw)

        # AND the balance of the minter is the balance sent.
        scenario.verify(minter.balance == sp.mutez(1))

    ################################################################
    # liquidate
    ################################################################

    # TODO(keefertaylor): Enable when SmartPy supports handling `failwith` in other contracts with `valid = False`
    # SEE: https://t.me/SmartPy_io/6538# 
    # @sp.add_test(name="liquidate - fails when not called from oven")
    # def test():
    #     scenario = sp.test_scenario()

    #     # GIVEN an OvenRegistry contract
    #     ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
    #     ovenRegistry = OvenRegistry.OvenRegistryContract(
    #         ovenFactoryContractAddress = ovenFactoryAddress
    #     )
    #     scenario += ovenRegistry

    #     # AND an oven which is registered
    #     ovenAddress = Addresses.OVEN_ADDRESS
    #     scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
    #         sender = ovenFactoryAddress
    #     )

    #     # AND a mock minter contract
    #     minter = MockMinter.MockMinterContract()
    #     scenario += minter

    #     # AND a faked Oracle contract
    #     fakeHarbingerValue = sp.nat(8)
    #     harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
    #     scenario += harbinger
    #     oracle = Oracle.OracleContract(
    #         harbingerContractAddress = harbinger.address
    #     )
    #     scenario += oracle

    #     # AND an OvenProxy
    #     ovenProxy = OvenProxyContract(
    #         ovenRegistryContractAddress = ovenRegistry.address,
    #         minterContractAddress = minter.address,
    #         oracleContractAddress = oracle.address
    #     )
    #     scenario += ovenProxy

    #     # WHEN borrow is called by someone other than an oven THEN the call fails.
    #     ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
    #     ovenBalance = sp.nat(1)
    #     borrowedTokens = sp.nat(2)
    #     isLiquidated = False
    #     stabilityFeeTokens = sp.int(3)
    #     interestIndex = sp.int(4)
    #     liquidatorAddress = Addresses.LIQUIDATOR_ADDRESS
    #     param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress)))))))
    #     amount = sp.mutez(1)
    #     scenario += ovenProxy.liquidate(param).run(
    #         sender = ownerAddress,
    #         amount = amount,
    #         valid = False
    #     )   

    @sp.add_test(name="liquidate - fails when paused")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy which is paused
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        liquidatorAddress = Addresses.LIQUIDATOR_ADDRESS
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.liquidate(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="liquidate - fails when in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE_STATE state
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        liquidatorAddress = Addresses.LIQUIDATOR_ADDRESS
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.liquidate(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="liquidate - passes liquidate params")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        liquidatorAddress = Addresses.LIQUIDATOR_ADDRESS
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, liquidatorAddress)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.liquidate(param).run(
            sender = ovenAddress,
            amount = amount,
            now = sp.timestamp_from_utc_now()
        )   

        # THEN the minter contract receives the parameters
        scenario.verify(minter.data.liquidate_ovenAddress == ovenAddress)
        scenario.verify(minter.data.liquidate_ownerAddress == ownerAddress)
        scenario.verify(minter.data.liquidate_ovenBalance == ovenBalance)
        scenario.verify(minter.data.liquidate_borrowedTokens == borrowedTokens)
        scenario.verify(minter.data.liquidate_liquidated == isLiquidated)
        scenario.verify(minter.data.liquidate_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(minter.data.liquidate_ovenInterestIndex == interestIndex)
        scenario.verify(minter.data.liquidate_liquidatorAddress == liquidatorAddress)

        # AND the balance of the minter is the balance sent.
        scenario.verify(minter.balance == sp.mutez(1))

    ################################################################
    # borrow
    ################################################################

    # TODO(keefertaylor): Enable when SmartPy supports handling `failwith` in other contracts with `valid = False`
    # SEE: https://t.me/SmartPy_io/6538
    # @sp.add_test(name="borrow - fails when not called from oven")
    # def test():
    #     scenario = sp.test_scenario()

    #     # GIVEN an OvenRegistry contract
    #     ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
    #     ovenRegistry = OvenRegistry.OvenRegistryContract(
    #         ovenFactoryContractAddress = ovenFactoryAddress
    #     )
    #     scenario += ovenRegistry

    #     # AND an oven which is registered
    #     ovenAddress = Addresses.OVEN_ADDRESS
    #     scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
    #         sender = ovenFactoryAddress
    #     )

    #     # AND a mock minter contract
    #     minter = MockMinter.MockMinterContract()
    #     scenario += minter

    #     # AND a faked Oracle contract
    #     fakeHarbingerValue = sp.nat(8)
    #     harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
    #     scenario += harbinger
    #     oracle = Oracle.OracleContract(
    #         harbingerContractAddress = harbinger.address
    #     )
    #     scenario += oracle

    #     # AND an OvenProxy
    #     ovenProxy = OvenProxyContract(
    #         ovenRegistryContractAddress = ovenRegistry.address,
    #         minterContractAddress = minter.address,
    #         oracleContractAddress = oracle.address
    #     )
    #     scenario += ovenProxy

    #     # WHEN borrow is called by someone other than an oven THEN the call fails.
    #     ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
    #     ovenBalance = sp.nat(1)
    #     borrowedTokens = sp.nat(2)
    #     isLiquidated = False
    #     stabilityFeeTokens = sp.int(3)
    #     interestIndex = sp.int(4)
    #     tokensToBorrow = sp.nat(5)
    #     param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow)))))))
    #     amount = sp.mutez(1)
    #     scenario += ovenProxy.borrow(param).run(
    #         sender = ownerAddress,
    #         amount = amount,
    #         valid = False
    #     )   

    @sp.add_test(name="borrow - fails when paused")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy which is paused
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToBorrow = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.borrow(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="borrow - fails when in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE_STATE state
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToBorrow = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.borrow(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="borrow - passes borrow params")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND a faked Oracle contract
        fakeHarbingerValue = sp.nat(8)
        harbinger = FakeHarbinger.FakeHarbingerContract(fakeHarbingerValue, sp.timestamp_from_utc_now(), "XTZ-USD")
        scenario += harbinger
        oracle = Oracle.OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address
        )
        scenario += ovenProxy

        # WHEN borrow is called by an oven
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToBorrow = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToBorrow)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.borrow(param).run(
            sender = ovenAddress,
            amount = amount,
            now = sp.timestamp_from_utc_now()
        )   

        # THEN the minter contract receives the parameters
        scenario.verify(minter.data.borrow_ovenAddress == ovenAddress)
        scenario.verify(minter.data.borrow_ownerAddress == ownerAddress)
        scenario.verify(minter.data.borrow_ovenBalance == ovenBalance)
        scenario.verify(minter.data.borrow_borrowedTokens == borrowedTokens)
        scenario.verify(minter.data.borrow_liquidated == isLiquidated)
        scenario.verify(minter.data.borrow_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(minter.data.borrow_ovenInterestIndex == interestIndex)
        scenario.verify(minter.data.borrow_tokensToBorrow == tokensToBorrow)

        # AND the balance of the minter is the balance sent.
        scenario.verify(minter.balance == sp.mutez(1))

    ################################################################
    # borrow_callback
    ################################################################

    @sp.add_test(name="borrow_callback - fails in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the IDLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = IDLE
        )
        scenario += ovenProxy

        # WHEN borrow_callback is called THEN the call fails
        callbackValue = sp.nat(2)
        scenario += ovenProxy.borrow_callback(callbackValue).run(
            sender = oracleAddress,
            valid = False
        )

    @sp.add_test(name="borrow_callback - fails with bad sender")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN borrow_callback is called by someone other than the oracle THEN the call fails
        callbackValue = sp.nat(2)
        notOracleAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        scenario += ovenProxy.borrow_callback(callbackValue).run(
            sender = notOracleAddress,
            valid = False
        )   

    ################################################################
    # liquidate_callback
    ################################################################

    @sp.add_test(name="liquidate_callback - fails in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the IDLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = IDLE
        )
        scenario += ovenProxy

        # WHEN liquidate_callback is called THEN the call fails
        callbackValue = sp.nat(2)
        scenario += ovenProxy.liquidate_callback(callbackValue).run(
            sender = oracleAddress,
            valid = False
        )

    @sp.add_test(name="liquidate_callback - fails with bad sender")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the LIQUIDATE_WAITING_FOR_ORACLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = LIQUIDATE_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN liquidate_callback is called by someone other than the oracle THEN the call fails
        callbackValue = sp.nat(2)
        notOracleAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        scenario += ovenProxy.liquidate_callback(callbackValue).run(
            sender = notOracleAddress,
            valid = False
        )        

    ################################################################
    # withdraw_callback
    ################################################################

    @sp.add_test(name="withdraw_callback - fails in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the IDLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = IDLE
        )
        scenario += ovenProxy

        # WHEN withdraw_callback is called THEN the call fails
        callbackValue = sp.nat(2)
        scenario += ovenProxy.withdraw_callback(callbackValue).run(
            sender = oracleAddress,
            valid = False
        )

    @sp.add_test(name="withdraw_callback - fails with bad sender")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an Oracle contract
        oracleAddress = Addresses.ORACLE_ADDRESS

        # AND an OvenProxy in the WITHDRAW_WAITING_FOR_ORACLE state
        ovenProxy = OvenProxyContract(
            minterContractAddress = minter.address,
            oracleContractAddress = oracleAddress,
            state = WITHDRAW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN withdraw_callback is called by someone other than the oracle THEN the call fails
        callbackValue = sp.nat(2)
        notOracleAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        scenario += ovenProxy.withdraw_callback(callbackValue).run(
            sender = notOracleAddress,
            valid = False
        )     

    ################################################################
    # repay
    ################################################################

    @sp.add_test(name="repay - fails when not sent from oven")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN repay is called by someone other than an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToRepay = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.repay(param).run(
            sender = ownerAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="repay - fails when paused")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy which is paused
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN repay is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToRepay = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.repay(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="repay - fails when in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE state
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN repay is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToRepay = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.repay(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="repay - passes repay params")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address
        )
        scenario += ovenProxy

        # WHEN repay is called by an oven
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        tokensToRepay = sp.nat(5)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex, tokensToRepay)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.repay(param).run(
            sender = ovenAddress,
            amount = amount
        )   

        # THEN the minter contract receives the parameters
        scenario.verify(minter.data.repay_ovenAddress == ovenAddress)
        scenario.verify(minter.data.repay_ownerAddress == ownerAddress)
        scenario.verify(minter.data.repay_ovenBalance == ovenBalance)
        scenario.verify(minter.data.repay_borrowedTokens == borrowedTokens)
        scenario.verify(minter.data.repay_liquidated == isLiquidated)
        scenario.verify(minter.data.repay_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(minter.data.repay_ovenInterestIndex == interestIndex)
        scenario.verify(minter.data.repay_tokensToRepay == tokensToRepay)

        # AND the balance of the minter is the balance sent.
        scenario.verify(minter.balance == sp.mutez(1))

    ################################################################
    # deposit
    ################################################################

    @sp.add_test(name="deposit - fails when not sent from oven")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN deposit is called by someone other than an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.deposit(param).run(
            sender = ownerAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="deposit - fails when paused")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy which is paused
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            paused = True
        )
        scenario += ovenProxy

        # WHEN deposit is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.deposit(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="deposit - fails when in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy in the BORROW_WAITING_FOR_ORACLE state
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            state = BORROW_WAITING_FOR_ORACLE
        )
        scenario += ovenProxy

        # WHEN deposit is called by an oven THEN the call fails.
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.deposit(param).run(
            sender = ovenAddress,
            amount = amount,
            valid = False
        )   

    @sp.add_test(name="deposit - passes deposit")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenRegistry contract
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryAddress
        )
        scenario += ovenRegistry

        # AND an oven which is registered
        ovenAddress = Addresses.OVEN_ADDRESS
        scenario += ovenRegistry.addOven((ovenAddress, ovenAddress)).run(
            sender = ovenFactoryAddress
        )

        # AND a mock minter contract
        minter = MockMinter.MockMinterContract()
        scenario += minter

        # AND an OvenProxy
        ovenProxy = OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address
        )
        scenario += ovenProxy

        # WHEN deposit is called by an oven
        ownerAddress = sp.address("tz1YfB2H1NoZVUq4heHqrVX4oVp99yz8gwNq")
        ovenBalance = sp.nat(1)
        borrowedTokens = sp.nat(2)
        isLiquidated = False
        stabilityFeeTokens = sp.int(3)
        interestIndex = sp.int(4)
        param = (ovenAddress, (ownerAddress, (ovenBalance, (borrowedTokens, (isLiquidated, (stabilityFeeTokens, (interestIndex)))))))
        amount = sp.mutez(1)
        scenario += ovenProxy.deposit(param).run(
            sender = ovenAddress,
            amount = amount
        )   

        # THEN the minter contract receives the parameters
        scenario.verify(minter.data.deposit_ovenAddress == ovenAddress)
        scenario.verify(minter.data.deposit_ownerAddress == ownerAddress)
        scenario.verify(minter.data.deposit_ovenBalance == ovenBalance)
        scenario.verify(minter.data.deposit_borrowedTokens == borrowedTokens)
        scenario.verify(minter.data.deposit_liquidated == isLiquidated)
        scenario.verify(minter.data.deposit_stabilityFeeTokens == stabilityFeeTokens)
        scenario.verify(minter.data.deposit_ovenInterestIndex == interestIndex)

        # AND the balance of the minter is the balance sent.
        scenario.verify(minter.balance == sp.mutez(1))

    ################################################################
    # updateState
    ################################################################

    @sp.add_test(name="updateState - successfully forwards update")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        minterContractAddress = Addresses.MINTER_ADDRESS
        ovenProxy = OvenProxyContract(
            minterContractAddress = minterContractAddress,
        )
        scenario += ovenProxy

        # AND an Oven contract.
        oven = Oven.OvenContract(
            ovenProxyContractAddress = ovenProxy.address
        )
        scenario += oven

        # WHEN updateState is called by the minter
        newBorrowedTokens = 1
        newStabilityFees = 2
        newInterestIndex = 3
        newIsLiquidated = True
        update = (oven.address, (newBorrowedTokens, (newStabilityFees, (newInterestIndex, newIsLiquidated))))
        scenario += ovenProxy.updateState(update).run(
            sender = minterContractAddress,
        )   

        # THEN the call is correctly forwarded to the Oven.
        scenario.verify(oven.data.borrowedTokens == newBorrowedTokens)
        scenario.verify(oven.data.stabilityFeeTokens == newStabilityFees)
        scenario.verify(oven.data.interestIndex == newInterestIndex)
        scenario.verify(oven.data.isLiquidated == newIsLiquidated)

    @sp.add_test(name="updateState - fails when not called by minter")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        minterContractAddress = Addresses.MINTER_ADDRESS
        ovenProxy = OvenProxyContract(
            minterContractAddress = minterContractAddress,
        )
        scenario += ovenProxy

        # WHEN updateState is called by someone who isn't the minter THEN the call fails
        notMinter = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        update = (notMinter, (1, (-2, (-3, True))))
        scenario += ovenProxy.updateState(update).run(
            sender = notMinter,
            valid = False
        )    

    ################################################################
    # pause
    ################################################################

    @sp.add_test(name="pause - succeeds when called by pause guardian")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        pauseGuardianContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            pauseGuardianContractAddress = pauseGuardianContractAddress,
            paused = False
        )
        scenario += ovenProxy

        # WHEN pause is called
        scenario += ovenProxy.pause(sp.unit).run(
            sender = pauseGuardianContractAddress
        )

        # THEN the contract is paused
        scenario.verify(ovenProxy.data.paused == True)

    @sp.add_test(name="pause - fails when not called by pause guardian")
    def test():
        # GIVEN an OvenProxy contract which is paused
        scenario = sp.test_scenario()

        pauseGuardianContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            pauseGuardianContractAddress = pauseGuardianContractAddress,
            paused = True
        )
        scenario += ovenProxy

        # WHEN pause is called by someone who isn't the pause guardian THEN the call fails
        notPauseGuardian = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.pause(sp.unit).run(
            sender = notPauseGuardian,
            valid = False
        )    

    ################################################################
    # unpause
    ################################################################

    @sp.add_test(name="unpause - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract which is paused
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress,
            paused = True
        )
        scenario += ovenProxy

        # WHEN unpause is called
        scenario += ovenProxy.unpause(sp.unit).run(
            sender = governorContractAddress
        )

        # THEN the contract is no longer paused.
        scenario.verify(ovenProxy.data.paused == False)

    @sp.add_test(name="unpause - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract which is paused
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress,
            paused = True
        )
        scenario += ovenProxy

        # WHEN unpause is called by someone who isn't the governor THEN the call fails
        notGovernor = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.unpause(sp.unit).run(
            sender = notGovernor,
            valid = False
        )    

    ################################################################
    # setGovernorContract
    ################################################################

    @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setGovernorContract is called with a new contract
        newContractAddress= sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setGovernorContract(newContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenProxy.data.governorContractAddress == newContractAddress)

    @sp.add_test(name="setGovernorContract - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
        newContractAddress = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setGovernorContract(newContractAddress).run(
            sender = newContractAddress,
            valid = False
        )    

    ################################################################
    # setMinterContract
    ################################################################

    @sp.add_test(name="setMinterContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setMinterContract is called with a new contract
        newContractAddress= sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setMinterContract(newContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenProxy.data.minterContractAddress == newContractAddress)

    @sp.add_test(name="setMinterContract - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setMinterContract is called by someone who isn't the governor THEN the call fails
        newContractAddress = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setMinterContract(newContractAddress).run(
            sender = newContractAddress,
            valid = False
        )    

    ################################################################
    # setOvenRegistryContract
    ################################################################

    @sp.add_test(name="setOvenRegistryContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setOvenRegistryContract is called with a new contract
        newContractAddress= sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setOvenRegistryContract(newContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenProxy.data.ovenRegistryContractAddress == newContractAddress)

    @sp.add_test(name="setOvenRegistryContract - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setOvenRegistryContract is called by someone who isn't the governor THEN the call fails
        newContractAddress = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setOvenRegistryContract(newContractAddress).run(
            sender = newContractAddress,
            valid = False
        )    

    ################################################################
    # setOracleContract
    ################################################################

    @sp.add_test(name="setOracleContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setOracleContract is called with a new contract
        newContractAddress= sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setOracleContract(newContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenProxy.data.oracleContractAddress == newContractAddress)

    @sp.add_test(name="setOracleContract - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setOracleContract is called by someone who isn't the governor THEN the call fails
        newContractAddress = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setOracleContract(newContractAddress).run(
            sender = newContractAddress,
            valid = False
        )    

    ################################################################
    # setPauseGuardian
    ################################################################

    @sp.add_test(name="setPauseGuardianContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setPauseGuardianContract is called with a new contract
        newContractAddress= sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setPauseGuardianContract(newContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenProxy.data.pauseGuardianContractAddress == newContractAddress)

    @sp.add_test(name="setPauseGuardianContract - fails when not called by governor")
    def test():
        # GIVEN an OvenProxy contract
        scenario = sp.test_scenario()

        governorContractAddress = sp.address("tz1harbiBBB9smBiDY7fV6DYpVm5aZD7HT98")
        ovenProxy = OvenProxyContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenProxy

        # WHEN the setPauseGuardianContract is called by someone who isn't the governor THEN the call fails
        newContractAddress = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")
        scenario += ovenProxy.setPauseGuardianContract(newContractAddress).run(
            sender = newContractAddress,
            valid = False
        )            

    sp.add_compilation_target("oven-proxy", OvenProxyContract())