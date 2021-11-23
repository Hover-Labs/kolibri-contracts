import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
DevFund = sp.io.import_script_from_url("file:dev-fund.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")

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
        savingsPoolContractAddress = Addresses.SAVINGS_ACCOUNT_ADDRESS,
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            governorContractAddress = governorContractAddress,
            administratorContractAddress = administratorContractAddress,
            tokenContractAddress = tokenContractAddress,
            ovenRegistryContractAddress = ovenRegistryContractAddress,
            savingsPoolContractAddress = savingsPoolContractAddress,

            # State machine
            state= DevFund.IDLE,
            sendAllTokens_destination = sp.none
        )

    ################################################################
    # Savings Account API
    ################################################################

    @sp.entry_point
    def accrueInterest(self, tokensAccrued):
        sp.set_type(tokensAccrued, sp.TNat)

        # Verify the caller is the savings account.
        sp.verify(sp.sender == self.data.savingsPoolContractAddress, message = Errors.NOT_SAVINGS_ACCOUNT)

        # Transfer the accrued tokens.
        tokenTransferParam = sp.record(
            from_ = sp.self_address,
            to_ = self.data.savingsPoolContractAddress, 
            value = tokensAccrued
        )
        transferHandle = sp.contract(
            sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
          self.data.tokenContractAddress,
          "transfer"
        ).open_some()
        sp.transfer(tokenTransferParam, sp.mutez(0), transferHandle)

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

    # Update the savings pool contract.
    @sp.entry_point
    def setSavingsPoolContract(self, newSavingsPoolContractAddress):
        sp.set_type(newSavingsPoolContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.savingsPoolContractAddress = newSavingsPoolContractAddress                

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    DummyContract = sp.io.import_script_from_url("file:test-helpers/dummy-contract.py")
    MockOvenProxy = sp.io.import_script_from_url("file:test-helpers/mock-oven-proxy.py")
    Oven = sp.io.import_script_from_url("file:oven.py")
    OvenRegistry = sp.io.import_script_from_url("file:oven-registry.py")
    Token = sp.io.import_script_from_url("file:token.py")

    ################################################################
    # accrueInterest
    ################################################################

    @sp.add_test(name="accrueInterest - can accrue interest")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a token contract.
        token = Token.FA12(
            admin = Addresses.TOKEN_ADMIN_ADDRESS
        )
        scenario += token
        
        # AND a StabilityFund contract
        savingsPoolContractAddress = Addresses.SAVINGS_ACCOUNT_ADDRESS
        fund = StabilityFundContract(
            savingsPoolContractAddress = savingsPoolContractAddress,
            tokenContractAddress = token.address
        )
        scenario += fund

        # AND the fund owns some tokens.
        scenario += token.mint(
            sp.record(
                address = fund.address,
                value = sp.nat(1000)
            )
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )

        # WHEN accrueInterest is called
        interestAccrued = sp.nat(123)
        scenario += fund.accrueInterest(interestAccrued).run(
            sender = Addresses.SAVINGS_ACCOUNT_ADDRESS
        )

        # THEN the savings account receives the tokens accrues.
        scenario.verify(token.data.balances[Addresses.SAVINGS_ACCOUNT_ADDRESS].balance == interestAccrued)

    @sp.add_test(name="accrueInterest - fails if not called by savings account")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a token contract.
        token = Token.FA12(
            admin = Addresses.TOKEN_ADMIN_ADDRESS
        )
        scenario += token
        
        # AND a StabilityFund contract
        savingsPoolContractAddress = Addresses.SAVINGS_ACCOUNT_ADDRESS
        fund = StabilityFundContract(
            savingsPoolContractAddress = savingsPoolContractAddress,
            tokenContractAddress = token.address
        )
        scenario += fund

        # AND the fund owns some tokens.
        scenario += token.mint(
            sp.record(
                address = fund.address,
                value = sp.nat(1000)
            )
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )

        # WHEN accrueInterest is called by someone other than the savings accounts
        # THEN the call fails
        notSavingsAccount = Addresses.NULL_ADDRESS
        interestAccrued = sp.nat(123)
        scenario += fund.accrueInterest(interestAccrued).run(
            sender = notSavingsAccount,
            valid = False
        )

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

    @sp.add_test(name="liquidate - fails if not a trusted oven")
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

        # WHEN liquidate is passed an address which is not an oven THEN the call fails.
        notOvenAddress = Addresses.NULL_ADDRESS
        scenario += fund.liquidate(notOvenAddress).run(
            sender = administrator,
            valid = False,
        )

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

    ################################################################
    # setSavingsAccountContract
    ################################################################

    @sp.add_test(name="setSavingsAccountContract - succeeds when called by governor")
    def test():
        # GIVEN an DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = StabilityFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setSavingsAccountContract is called with a new contract
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setSavingsAccountContract(rotatedAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(fund.data.savingsPoolContractAddress == rotatedAddress)

    @sp.add_test(name="setSavingsAccountContract - fails when not called by governor")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = StabilityFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setSavingsAccountContract is called by someone who isn't the governor THEN the call fails
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setSavingsAccountContract(rotatedAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )        
        
    sp.add_compilation_target("stability-fund", StabilityFundContract())