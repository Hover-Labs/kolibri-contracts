import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")

################################################################
# Contract
################################################################

class DevFundContract(sp.Contract):
    def __init__(
        self, 
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,
        administratorContractAddress = Addresses.FUND_ADMINISTRATOR_ADDRESS,
        tokenContractAddress = Addresses.TOKEN_ADDRESS,
        **extra_storage
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            governorContractAddress = governorContractAddress,
            administratorContractAddress = administratorContractAddress,
            tokenContractAddress = tokenContractAddress,
            **extra_storage
        )

    ################################################################
    # Public API
    ################################################################

    # Allow transfers into the fund as a consequence of liquidation.
    @sp.entry_point
    def default(self):
        pass

    ################################################################
    # Administrator API
    ################################################################

    @sp.entry_point
    def setDelegate(self, newDelegate):
        sp.set_type(newDelegate, sp.TOption(sp.TKeyHash))

        # Verify the caller is the admin.
        sp.verify(sp.sender == self.data.administratorContractAddress, message = Errors.NOT_ADMIN)

        sp.set_delegate(newDelegate)

    ################################################################
    # Governance
    ################################################################

    # Governance is timelocked and can always transfer funds.
    @sp.entry_point
    def send(self, param):
        sp.set_type(param, sp.TPair(sp.TMutez, sp.TAddress))

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        sp.send(sp.snd(param), sp.fst(param))

    # Governance is timelocked and can always transfer funds.
    @sp.entry_point
    def sendTokens(self, param):
        sp.set_type(param, sp.TPair(sp.TNat, sp.TAddress))

        # Verify sender is governor.
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        # Destructure parameters.
        amount = sp.fst(param)
        destination = sp.snd(param)

        # Invoke token contract
        tokenContractParam = sp.record(
            to_ = destination,
            from_ = sp.self_address,
            value = amount
        )
        contractHandle = sp.contract(
            sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
            self.data.tokenContractAddress,
            "transfer"
        ).open_some()
        sp.transfer(tokenContractParam, sp.mutez(0), contractHandle)

    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # Update the administrator contract.
    @sp.entry_point
    def setAdministratorContract(self, newAdministratorContractAddress):
        sp.set_type(newAdministratorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.administratorContractAddress = newAdministratorContractAddress

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
    # default
    ################################################################

    @sp.add_test(name="default - can receive funds")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        fund = DevFundContract()
        scenario += fund

        # WHEN the default entry point is called
        amount = sp.mutez(1)
        scenario += fund.default(sp.unit).run(
            amount = amount,
        )

        # THEN the funds are accepted.
        scenario.verify(fund.balance == amount)

    ################################################################
    # setDelegate
    ################################################################

    @sp.add_test(name="setDelegate - fails when not called by administrator")
    def test():
        # GIVEN a DevFund without a delegate and an administrator.
        scenario = sp.test_scenario()
        administrator = Addresses.FUND_ADMINISTRATOR_ADDRESS

        fund = DevFundContract(
            administratorContractAddress = administrator
        )
        scenario += fund

        # WHEN setDelegate is called by someone other than the administrator THEN the invocation fails.
        notAdministrator = Addresses.NULL_ADDRESS
        delegate = sp.some(Addresses.BAKER_KEY_HASH)
        scenario += fund.setDelegate(delegate).run(
            sender = notAdministrator,
            voting_powers = Addresses.VOTING_POWERS,
            valid = False
        )

    @sp.add_test(name="setDelegate - updates delegate")
    def test():
        # GIVEN a DevFund contract without a delegate and an administrator.
        scenario = sp.test_scenario()
        administrator = Addresses.FUND_ADMINISTRATOR_ADDRESS

        fund = DevFundContract(
            administratorContractAddress = administrator
        )
        scenario += fund

        # WHEN setDelegate is called by the administrator
        delegate = sp.some(Addresses.BAKER_KEY_HASH)
        scenario += fund.setDelegate(delegate).run(
            sender = administrator,
            voting_powers = Addresses.VOTING_POWERS
        )

        # THEN the delegate is updated.
        scenario.verify(fund.baker.open_some() == delegate.open_some())

    ################################################################
    # send
    ################################################################

    @sp.add_test(name="send - succeeds when called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a DevFund contract with some balance
        balance = sp.mutez(10)
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        fund.set_initial_balance(balance)
        scenario += fund

        # AND a dummy contract to receive funds
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN send is called
        param = (balance, dummyContract.address)
        scenario += fund.send(param).run(
            sender = governorContractAddress,
        )

        # THEN the funds are sent.
        scenario.verify(fund.balance == sp.mutez(0))
        scenario.verify(dummyContract.balance == balance)

    @sp.add_test(name="send - fails when not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a DevFund contract
        balance = sp.mutez(10)
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        fund.set_initial_balance(balance)
        scenario += fund

        # WHEN send is called by someone who isn't the governor THEN the call fails
        notGovernor = Addresses.NULL_ADDRESS
        param = (balance, notGovernor)
        scenario += fund.send(param).run(
            sender = notGovernor,
            valid = False
        )    
    ################################################################
    # sendTokens
    ################################################################

    @sp.add_test(name="sendTokens - succeeds when called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address
        )
        scenario += fund

        # And a dummy contract to send to.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendTokens is called
        amount = sp.nat(200)
        param = (amount, dummyContract.address)
        scenario += fund.sendTokens(param).run(
            sender = governorAddress,
        )

        # THEN the fund is debited tokens
        scenario.verify(token.data.balances[fund.address].balance == sp.as_nat(fundTokens - amount))

        # AND the receiver was credited the tokens.
        scenario.verify(token.data.balances[dummyContract.address].balance == amount)

    @sp.add_test(name="sendTokens - fails when not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendTokens is called by someone who isn't the governor THEN the call fails.
        notGovernor = Addresses.NULL_ADDRESS
        amount = sp.nat(200)
        param = (amount, Addresses.ROTATED_ADDRESS)
        scenario += fund.sendTokens(param).run(
            sender = notGovernor,
            valid = False
        )

    ################################################################
    # setGovernorContract
    ################################################################

    @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setGovernorContract is called with a new contract
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setGovernorContract(rotatedAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(fund.data.governorContractAddress == rotatedAddress)

    @sp.add_test(name="setGovernorContract - fails when not called by governor")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setGovernorContract(rotatedAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    ################################################################
    # setAdministratorContract
    ################################################################

    @sp.add_test(name="setAdministratorContract - succeeds when called by governor")
    def test():
        # GIVEN an DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setAdministratorContract is called with a new contract
        rotatedAddress= Addresses.ROTATED_ADDRESS
        scenario += fund.setAdministratorContract(rotatedAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(fund.data.administratorContractAddress == rotatedAddress)

    @sp.add_test(name="setAdministratorContract - fails when not called by governor")
    def test():
        # GIVEN a DevFund contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # WHEN the setAdministratorContract is called by someone who isn't the governor THEN the call fails
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += fund.setAdministratorContract(rotatedAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    sp.add_compilation_target("dev-fund", DevFundContract())
