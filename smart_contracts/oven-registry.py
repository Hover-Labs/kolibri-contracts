import smartpy as sp

Addresses = sp.import_script_from_url("file:test-helpers/addresses.py")
Errors = sp.import_script_from_url("file:common/errors.py")

################################################################
# Contract
################################################################

class OvenRegistryContract(sp.Contract):
    def __init__(
        self,
        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS,  
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,  
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            governorContractAddress = governorContractAddress, 
            ovenFactoryContractAddress = ovenFactoryContractAddress,
            ovenMap = sp.big_map(
                l = {},
                tkey=sp.TAddress,
                tvalue=sp.TAddress
            )
        )

    ################################################################
    # Public Interface
    ################################################################

    @sp.entry_point
    def isOven(self, maybeOvenAddress):
        sp.verify(self.data.ovenMap.contains(maybeOvenAddress), message = Errors.NOT_OVEN)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

    # Disallow direct transfers.
    @sp.entry_point
    def default(self, param):
        sp.set_type(param, sp.TUnit)
        sp.failwith(Errors.CANNOT_RECEIVE_FUNDS)        

    ################################################################
    # OvenFactory Interface
    ################################################################

    # (oven address, owner)
    @sp.entry_point
    def addOven(self, param):
        sp.set_type(param, sp.TPair(sp.TAddress, sp.TAddress))

        sp.verify(sp.sender == self.data.ovenFactoryContractAddress, message = Errors.NOT_OVEN_FACTORY)

        ovenAddress = sp.fst(param)
        owner = sp.snd(param)

        self.data.ovenMap[ovenAddress] = owner

    ################################################################
    # Governance
    ################################################################

    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # Update the oven factory contract address.
    @sp.entry_point
    def setOvenFactoryContract(self, newOvenFactoryContract):
        sp.set_type(newOvenFactoryContract, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenFactoryContractAddress = newOvenFactoryContract


# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    ################################################################
    # isOven
    ################################################################

    @sp.add_test(name="isOven - fails with unknown oven")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryContractAddress
        )
        scenario += ovenRegistry

        # AND an oven that is registered in the OvenRegistry
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        addOvenParameter = (ovenAddress, ownerAddress)
        scenario += ovenRegistry.addOven(addOvenParameter).run(
            sender = ovenFactoryContractAddress
        )

        # WHEN isOven is called for an unregistered oven THEN the invocation fails.
        notOven = Addresses.NULL_ADDRESS
        scenario += ovenRegistry.isOven(notOven).run(
            valid = False
        )

    @sp.add_test(name="isOven - succeeds with known oven")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryContractAddress
        )
        scenario += ovenRegistry

        # AND an oven that is registered in the OvenRegistry
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        addOvenParameter = (ovenAddress, ownerAddress)
        scenario += ovenRegistry.addOven(addOvenParameter).run(
            sender = ovenFactoryContractAddress
        )

        # WHEN isOven is called for the oven THEN the invocation does not fail
        scenario += ovenRegistry.isOven(ovenAddress)

    @sp.add_test(name="isOven - fails with known oven and an amount")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryContractAddress
        )
        scenario += ovenRegistry

        # AND an oven that is registered in the OvenRegistry
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        addOvenParameter = (ovenAddress, ownerAddress)
        scenario += ovenRegistry.addOven(addOvenParameter).run(
            sender = ovenFactoryContractAddress
        )

        # WHEN isOven is called for the oven with an amount THEN the invocation does not fail
        scenario += ovenRegistry.isOven(ovenAddress).run(
            amount = sp.mutez(1),
            valid = False
        )

    ################################################################
    # addOven
    ################################################################

    @sp.add_test(name="addOven - fails when not called by OvenFactory")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryContractAddress
        )
        scenario += ovenRegistry

        # WHEN an oven is added to the contract by another contract THEN the invocation fails.
        notOvenFactory = Addresses.NULL_ADDRESS

        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        addOvenParameter = (ovenAddress, ownerAddress)

        scenario += ovenRegistry.addOven(addOvenParameter).run(
            sender = notOvenFactory,
            valid = False
        )

    @sp.add_test(name="addOven - succeeds")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenFactoryContractAddress = Addresses.OVEN_FACTORY_ADDRESS
        ovenRegistry = OvenRegistryContract(
            ovenFactoryContractAddress = ovenFactoryContractAddress
        )
        scenario += ovenRegistry

        # WHEN an oven is added to the contract
        ovenAddress = Addresses.OVEN_ADDRESS
        ownerAddress = Addresses.OVEN_OWNER_ADDRESS
        addOvenParameter = (ovenAddress, ownerAddress)
        scenario += ovenRegistry.addOven(addOvenParameter).run(
            sender = ovenFactoryContractAddress,
        )

        # THEN the OvenRegistry is registered in the registry's map.
        scenario.verify(ovenRegistry.data.ovenMap[ovenAddress] == ownerAddress)

        # AND future calls to isOven report the oven as registered.
        scenario += ovenRegistry.isOven(ovenAddress)

    ################################################################
    # default
    ################################################################

    @sp.add_test(name="default - fails with calls to the default entrypoint")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        ovenRegistry = OvenRegistryContract()
        scenario += ovenRegistry

        # WHEN a transfer is made THEN the invocation fails.
        scenario += ovenRegistry.default().run(
            amount = sp.mutez(0),
            valid = False
        )

    ################################################################
    # setGovernorContract
    ################################################################

    @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # WHEN the setGovernorContract is called with a new governor contract
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenRegistry.setGovernorContract(newGovernorContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the governor contract is updated.
        scenario.verify(ovenRegistry.data.governorContractAddress == newGovernorContractAddress)

    @sp.add_test(name="setGovernorContract - fails when not called by governor")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
        newGovernorContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenRegistry.setGovernorContract(newGovernorContractAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )

    ################################################################
    # setOvenFactoryContract
    ################################################################

    @sp.add_test(name="setOvenFactoryContract - succeeds when called by governor")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # WHEN the setOvenFactoryContract is called with a new governor contract
        newOvenFactoryContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenRegistry.setOvenFactoryContract(newOvenFactoryContractAddress).run(
            sender = governorContractAddress,
        )

        # THEN the governor contract is updated.
        scenario.verify(ovenRegistry.data.ovenFactoryContractAddress == newOvenFactoryContractAddress)

    @sp.add_test(name="setOvenFactoryContract - fails when not called by governor")
    def test():
        # GIVEN an OvenRegistry contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        # WHEN the setOvenFactoryContract is called by someone who isn't the governor THEN the call fails
        newOvenFactoryContractAddress = Addresses.ROTATED_ADDRESS
        scenario += ovenRegistry.setOvenFactoryContract(newOvenFactoryContractAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    
