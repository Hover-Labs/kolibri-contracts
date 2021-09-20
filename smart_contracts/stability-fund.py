import smartpy as sp

Addresses = sp.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.import_script_from_url("file:common/constants.py")
DevFund = sp.import_script_from_url("file:dev-fund.py")
Errors = sp.import_script_from_url("file:common/errors.py")

################################################################
# Contract
################################################################

# Extends `DeveloperFund` with the additional ability for the Administrator
# to liquidate Ovens.
class StabilityFundContract(DevFund.DevFundContract):
    def __init__(
        self, 
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,
        administratorContractAddress = Addresses.FUND_ADMINISTRATOR_ADDRESS,
        ovenRegistryContractAddress = Addresses.OVEN_REGISTRY_ADDRESS,
        tokenContractAddress = Addresses.TOKEN_ADDRESS,
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            governorContractAddress = governorContractAddress,
            administratorContractAddress = administratorContractAddress,
            tokenContractAddress = tokenContractAddress,
            ovenRegistryContractAddress = ovenRegistryContractAddress
        )

    ################################################################
    # Administrator API
    ################################################################

    @sp.entry_point
    def liquidate(self, ovenAddress):
        sp.set_type(ovenAddress, sp.TAddress)

        # Verify the caller is the admin.
        sp.verify(sp.sender == self.data.administratorContractAddress, message = Errors.NOT_ADMIN)

        # Verify the liquidation target is a trusted oven.
        contractHandle = sp.contract(
            sp.TAddress,
            self.data.ovenRegistryContractAddress,
            "isOven"
        ).open_some()
        sp.transfer(ovenAddress, sp.mutez(0), contractHandle)

        # Liquidate oven
        contractHandle = sp.contract(
            sp.TUnit,
            ovenAddress,
            "liquidate"
        ).open_some()
        sp.transfer(sp.unit, sp.mutez(0), contractHandle)

    ################################################################
    # Governance
    ################################################################

    # Update the oven registry contract.
    @sp.entry_point
    def setOvenRegistryContract(self, newOvenRegistryContractAddress):
        sp.set_type(newOvenRegistryContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.ovenRegistryContractAddress = newOvenRegistryContractAddress        

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    DummyContract = sp.import_script_from_url("file:test-helpers/dummy-contract.py")
    MockOvenProxy = sp.import_script_from_url("file:test-helpers/mock-oven-proxy.py")
    Oven = sp.import_script_from_url("file:oven.py")
    OvenRegistry = sp.import_script_from_url("file:oven-registry.py")
    Token = sp.import_script_from_url("file:token.py")

    ################################################################
    # liquidate
    ################################################################

    @sp.add_test(name="liquidate - can liquidate oven")
    def test():
      scenario = sp.test_scenario()

      # GIVEN an OvenRegistry contract
      ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS
      ovenRegistry = OvenRegistry.OvenRegistryContract(
          ovenFactoryContractAddress = ovenFactoryAddress
      )
      scenario += ovenRegistry

      # AND a mock oven proxy contract.
      ovenProxy = MockOvenProxy.MockOvenProxyContract()
      scenario += ovenProxy

      # AND an oven with a balance
      balance = sp.mutez(12)
      oven = Oven.OvenContract(
          ovenProxyContractAddress = ovenProxy.address
      )
      oven.set_initial_balance(balance)
      scenario += oven

      # AND the oven is registered
      scenario += ovenRegistry.addOven((oven.address, oven.address)).run(
          sender = ovenFactoryAddress
      )

      # AND a StabilityFund contract
      administrator = Addresses.FUND_ADMINISTRATOR_ADDRESS
      fund = StabilityFundContract(
          administratorContractAddress = administrator,
          ovenRegistryContractAddress = ovenRegistry.address
      )
      scenario += fund

      # WHEN liquidate is called by an address tht is not the administrator
      scenario += fund.liquidate(oven.address).run(
          sender = administrator,
      )

      # THEN the balance was transferred to the MockOvenProxy.
      scenario.verify(ovenProxy.balance == balance)

    @sp.add_test(name="liquidate - fails if not called by admin")
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

      # AND a StabilityFund contract
      administrator = Addresses.FUND_ADMINISTRATOR_ADDRESS
      fund = StabilityFundContract(
          administratorContractAddress = administrator,
          ovenRegistryContractAddress = ovenRegistry.address
      )
      scenario += fund

      # WHEN liquidate is called by an address that is not the administrator THEN the call fails.
      notAdministrator = Addresses.NULL_ADDRESS
      scenario += fund.liquidate(ovenAddress).run(
          sender = notAdministrator,
          valid = False,
      )

    # TODO(keefertaylor): Enable when SmartPy supports handling `failwith` in other contracts with `valid = False`
    # SEE: https://t.me/SmartPy_io/6538@sp.add_test(name="oven-factory-withdraw - fails when not called from oven")
    # @sp.add_test(name="liquidate - fails if not a trusted oven")
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

    #     # AND a StabilityFund contract
    #     administrator = Addresses.FUND_ADMINISTRATOR_ADDRESS
    #     fund = StabilityFundContract(
    #         administratorContractAddress = administrator,
    #         ovenRegistryContractAddress = ovenRegistry.address
    #     )
    #     scenario += fund

    #     # WHEN liquidate is passed an address which is not an oven THEN the call fails.
    #     notOvenAddress = Addresses.NULL_ADDRESS
    #     scenario += fund.liquidate(notOvenAddress).run(
    #         sender = administrator,
    #         valid = False,
    #     )

    ################################################################
    # setOvenRegistryContract
    ################################################################

    @sp.add_test(name="setOvenRegistryContract - succeeds when called by governor")
    def test():
        # GIVEN an DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = StabilityFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setOvenRegistryContract is called with a new contract
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setOvenRegistryContract(rotatedAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(fund.data.ovenRegistryContractAddress == rotatedAddress)

    @sp.add_test(name="setOvenRegistryContract - fails when not called by governor")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = StabilityFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setOvenRegistryContract is called by someone who isn't the governor THEN the call fails
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setOvenRegistryContract(rotatedAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    