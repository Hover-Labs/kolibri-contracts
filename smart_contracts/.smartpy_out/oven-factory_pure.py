import smartpy as sp

Addresses = sp.import_script_from_url("file:test-helpers/addresses.py")
Errors = sp.import_script_from_url("file:common/errors.py")
Oven = sp.import_script_from_url("file:oven.py")

################################################################
# State Machine States.
################################################################

IDLE = 0
WAITING_FOR_INTEREST_INDEX = 1

################################################################
# Contract
################################################################

class OvenFactoryContract(sp.Contract):
    def __init__(
        self, 
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,  
        ovenRegistryContractAddress = Addresses.OVEN_REGISTRY_ADDRESS,
        ovenProxyContractAddress = Addresses.OVEN_PROXY_ADDRESS,
        minterContractAddress = Addresses.MINTER_ADDRESS,
        state = IDLE,
        makeOvenOwner = sp.none,
        initialDelegate = sp.some(sp.key_hash("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf"))
    ):
        self.ovenContract = Oven.OvenContract()

        self.exception_optimization_level = "DefaultUnit"

        self.init(
            governorContractAddress = governorContractAddress,
            ovenProxyContractAddress = ovenProxyContractAddress,
            ovenRegistryContractAddress = ovenRegistryContractAddress,
            initialDelegate = initialDelegate,
            state = state,
            minterContractAddress = minterContractAddress,

            # registers
            makeOvenOwner = makeOvenOwner
        )

    ################################################################
    # Public Interface
    ################################################################

    @sp.entry_point
    def makeOven(self, param):
        sp.set_type(param, sp.TUnit)

        # Ensure contract is IDLE.
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Update state and save sender
        self.data.state = WAITING_FOR_INTEREST_INDEX
        self.data.makeOvenOwner = sp.some(sp.sender)

        # Call Minter contract.
        callback = sp.self_entry_point(entry_point = "makeOven_minterCallback")
        minterContractHandle = sp.contract(
            sp.TContract(sp.TNat),
            self.data.minterContractAddress,
            'getInterestIndex'
        ).open_some()
        sp.transfer(callback, sp.mutez(0), minterContractHandle)

    # Disallow direct transfers.
    @sp.entry_point
    def default(self, param):
        sp.set_type(param, sp.TUnit)
        sp.failwith(Errors.CANNOT_RECEIVE_FUNDS)        

    ################################################################
    # Minter Interface
    ################################################################

    @sp.entry_point
    def makeOven_minterCallback(self, param):
        sp.set_type(param, sp.TNat)

        # Verify sender was Minter.
        sp.verify(sp.sender == self.data.minterContractAddress, message = Errors.NOT_MINTER)

        # Verify in correct state.
        sp.verify(self.data.state == WAITING_FOR_INTEREST_INDEX, message = Errors.BAD_STATE)
        ovenOwner = self.data.makeOvenOwner.open_some()

        # Originate a new oven contract
        storage = sp.record(
            borrowedTokens = sp.nat(0),
            interestIndex = sp.to_int(param),
            isLiquidated = False,
            ovenProxyContractAddress = self.data.ovenProxyContractAddress,
            owner = ovenOwner,
            stabilityFeeTokens = sp.int(0),
        )
        newContract = sp.create_contract(storage = storage, contract = self.ovenContract, baker = self.data.initialDelegate)

        # Add the contract to the oven registry.
        registryParam = (newContract, ovenOwner)
        ovenRegistryHandle = sp.contract(
            sp.TPair(sp.TAddress, sp.TAddress),
            self.data.ovenRegistryContractAddress,
            'addOven'
        ).open_some()
        sp.transfer(registryParam, sp.mutez(0), ovenRegistryHandle)

        # Reset state
        self.data.state = IDLE
        self.data.makeOvenOwner = sp.none

    ################################################################
    # Governance Functions
    ################################################################

    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # Update the oven registry contract address.
    @sp.entry_point
    def setOvenRegistryContract(self, newOvenRegistryContractAddress):
        sp.set_type(newOvenRegistryContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenRegistryContractAddress = newOvenRegistryContractAddress        

    # Update the oven proxy contract address.
    @sp.entry_point
    def setOvenProxyContract(self, newOvenProxyContractAddress):
        sp.set_type(newOvenProxyContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenProxyContractAddress = newOvenProxyContractAddress

    # Update the minter contract address.
    @sp.entry_point
    def setMinterContract(self, newMinterContract):
        sp.set_type(newMinterContract, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.minterContractAddress = newMinterContract

    # Update the initial delegate address.
    @sp.entry_point
    def setInitialDelegate(self, newInitialDelegate):
        sp.set_type(newInitialDelegate, sp.TOption(sp.TKeyHash))

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.initialDelegate = newInitialDelegate

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    Minter = sp.import_script_from_url("file:minter.py")
    OvenRegistry = sp.import_script_from_url("file:oven-registry.py")

    ################################################################
    # makeOven
    ################################################################

    @sp.add_test(name="makeOven succeeds")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND a Minter contract.
        minter = Minter.MinterContract(
            governorContractAddress = governorContractAddress
        )
        scenario += minter

        # AND an OvenFactory contract
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minter.address,
            ovenRegistryContractAddress = ovenRegistry.address,
            state = IDLE,
            makeOvenOwner = sp.none
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven is called THEN the request succeeds.
        ovenOwner =  Addresses.OVEN_OWNER_ADDRESS
        scenario += ovenFactory.makeOven(sp.unit).run(
            now = sp.timestamp_from_utc_now(),
            sender = ovenOwner
        )

    @sp.add_test(name="makeOven - fails in bad state")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND a Minter contract.
        minter = Minter.MinterContract(
            governorContractAddress = governorContractAddress
        )
        scenario += minter

        # AND an OvenFactory contract in the WAITING_FOR_INTEREST_INDEX state
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minter.address,
            ovenRegistryContractAddress = ovenRegistry.address,
            state = WAITING_FOR_INTEREST_INDEX,
            makeOvenOwner = sp.none
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven is called THEN the request fails.
        ovenOwner =  Addresses.OVEN_OWNER_ADDRESS
        scenario += ovenFactory.makeOven(sp.unit).run(
            sender = ovenOwner,
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    @sp.add_test(name="makeOven - fails with amount attached")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND a Minter contract.
        minter = Minter.MinterContract(
            governorContractAddress = governorContractAddress
        )
        scenario += minter

        # AND an OvenFactory contract
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minter.address,
            ovenRegistryContractAddress = ovenRegistry.address,
            state = IDLE,
            makeOvenOwner = sp.none
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven is called with an amount THEN the request fails.
        ovenOwner =  Addresses.OVEN_OWNER_ADDRESS
        scenario += ovenFactory.makeOven(sp.unit).run(
            sender = ovenOwner,
            amount = sp.mutez(1),
            now = sp.timestamp_from_utc_now(),
            valid = False
        )

    ###############################################################
    # makeOven_minterCallback
    ###############################################################

    @sp.add_test(name="makeOven_minterCallback - fails when not called from minter")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND an OvenFactory contract
        ovenOwner = sp.some(Addresses.OVEN_OWNER_ADDRESS)
        minterContractAddress = Addresses.MINTER_ADDRESS
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minterContractAddress,
            ovenRegistryContractAddress = ovenRegistry.address,
            state = WAITING_FOR_INTEREST_INDEX,
            makeOvenOwner = ovenOwner
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven_minterCallback entry point is called by someone other than the minter THEN the request fails
        interestIndex = 1
        notMinter = Addresses.NULL_ADDRESS
        scenario += ovenFactory.makeOven_minterCallback(interestIndex).run(
            sender = notMinter,
            valid = False
        )

    @sp.add_test(name="makeOven_minterCallback - fails when called in bad state")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND an OvenFactory contract in the IDLE state
        minterContractAddress = Addresses.MINTER_ADDRESS
        ovenOwner = sp.some(Addresses.OVEN_OWNER_ADDRESS)
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minterContractAddress,
            state = IDLE,
            makeOvenOwner = ovenOwner
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven_minterCallback entry point is called THEN the request fails
        interestIndex = 1
        scenario += ovenFactory.makeOven_minterCallback(interestIndex).run(
            sender = minterContractAddress,
            valid = False
        )

    @sp.add_test(name="makeOven_minterCallback - succeeds and resets state")
    def test():
        scenario = sp.test_scenario()
        
        # GIVEN an OvenRegistry contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # AND an OvenFactory contract in the IDLE state
        minterContractAddress = Addresses.MINTER_ADDRESS
        ovenOwner = sp.some(Addresses.OVEN_OWNER_ADDRESS)
        ovenFactory = OvenFactoryContract(
            minterContractAddress = minterContractAddress,
            state = WAITING_FOR_INTEREST_INDEX,
            makeOvenOwner = ovenOwner
        )
        scenario += ovenFactory

        # AND OvenRegistry is bound to OvenFactory
        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )

        # WHEN the makeOven_minterCallback entry point is called
        interestIndex = sp.nat(1)
        scenario += ovenFactory.makeOven_minterCallback(interestIndex).run(
            sender = minterContractAddress,
        )        

        # THEN the call succeeds and the state is reset.
        scenario.verify(ovenFactory.data.state == IDLE)
        scenario.verify(ovenFactory.data.makeOvenOwner.is_some() == False)

    ################################################################
    # default
    ################################################################

    @sp.add_test(name="default - fails with calls to the default entrypoint")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the default entry point is called THEN the request fails
        scenario += ovenFactory.default(sp.unit).run(
            amount = sp.mutez(1),
            valid = False
        )

    ################################################################
    # setGovernorContract
    ################################################################

    @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setGovernorContract is called with a new contract
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setGovernorContract(newGovernorContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenFactory.data.governorContractAddress == newGovernorContractAddress)

    @sp.add_test(name="setGovernorContract - fails when not called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setGovernorContract(newGovernorContractAddress).run(
            sender = newGovernorContractAddress,
            valid = False
        )    

    ################################################################
    # setOvenRegistryContract
    ################################################################

    @sp.add_test(name="setOvenRegistryContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setOvenRegistryContract is called with a new contract
        newOvenRegistryContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setOvenRegistryContract(newOvenRegistryContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenFactory.data.ovenRegistryContractAddress == newOvenRegistryContractAddress)

    @sp.add_test(name="setOvenRegistryContract - fails when not called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setOvenRegistryContract is called by someone who isn't the governor THEN the call fails
        newOvenRegistryContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setOvenRegistryContract(newOvenRegistryContractAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    ################################################################
    # setOvenProxyContract
    ################################################################

    @sp.add_test(name="setOvenProxyContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setOvenProxyContract is called with a new contract
        newOvenProxyContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setOvenProxyContract(newOvenProxyContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenFactory.data.ovenProxyContractAddress == newOvenProxyContractAddress)

    @sp.add_test(name="setOvenProxyContract - fails when not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an OvenFactory contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setOvenProxyContract is called by someone who isn't the governor THEN the call fails
        newOvenProxyContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setOvenProxyContract(newOvenProxyContractAddress).run(
            sender = newOvenProxyContractAddress,
            valid = False
        )    

    ################################################################
    # setMinterContract
    ################################################################

    @sp.add_test(name="setMinterContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setMinterContract is called with a new contract
        newMinterContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setMinterContract(newMinterContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenFactory.data.minterContractAddress == newMinterContractAddress)

    @sp.add_test(name="setMinterContract - fails when not called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setMinterContract is called by someone who isn't the governor THEN the call fails
        newMinterContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenFactory.setMinterContract(newMinterContractAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    ################################################################
    # setInitialDelegate
    ################################################################

    @sp.add_test(name="setInitialDelegate - succeeds when called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress,
            initialDelegate = sp.none
        )
        scenario += ovenFactory

        # WHEN the setInitialDelegate is called with a new contract
        newInitialDelegate = sp.some(sp.key_hash("tz1NRTQeqcuwybgrZfJavBY3of83u8uLpFBj"))
        scenario += ovenFactory.setInitialDelegate(newInitialDelegate).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(ovenFactory.data.initialDelegate.open_some() == newInitialDelegate.open_some())

    @sp.add_test(name="setInitialDelegate - fails when not called by governor")
    def test():
        # GIVEN an OvenFactory contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenFactory = OvenFactoryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenFactory

        # WHEN the setInitialDelegate is called by someone who isn't the governor THEN the call fails
        newInitialDelegate = sp.some(sp.key_hash("tz1NRTQeqcuwybgrZfJavBY3of83u8uLpFBj"))
        scenario += ovenFactory.setInitialDelegate(newInitialDelegate).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

