import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")

################################################################
# State Machine
################################################################

IDLE = 0
WAITING_FOR_TOKEN_BALANCE = 1

################################################################
# Contract
################################################################

class DevFundContract(sp.Contract):
    def __init__(
        self, 
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,
        administratorContractAddress = Addresses.FUND_ADMINISTRATOR_ADDRESS,
        tokenContractAddress = Addresses.TOKEN_ADDRESS,
        state = IDLE,
        sendAllTokens_destination = sp.none,
        **extra_storage
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            # Addresses
            governorContractAddress = governorContractAddress,
            administratorContractAddress = administratorContractAddress,
            tokenContractAddress = tokenContractAddress,

            # State machine
            state = state,
            sendAllTokens_destination = sendAllTokens_destination,

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
    def sendAll(self, destination):
        sp.set_type(destination, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        sp.send(destination, sp.balance)        

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

    # Transfer the entire balance of kUSD
    @sp.entry_point
    def sendAllTokens(self, destination):
        sp.set_type(destination, sp.TAddress)

        # Verify sender is governor.
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        # Verify state is correct.
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Call token contract to get the balance
        tokenContractHandle = sp.contract(
            sp.TPair(
                sp.TAddress,
                sp.TContract(sp.TNat),
            ),
            self.data.tokenContractAddress,
            "getBalance"
        ).open_some()
        tokenContractArg = (
            sp.self_address,
            sp.self_entry_point(entry_point = "sendAllTokens_callback")
        )
        sp.transfer(tokenContractArg, sp.mutez(0), tokenContractHandle)

        # Save state to state machine
        self.data.state = WAITING_FOR_TOKEN_BALANCE
        self.data.sendAllTokens_destination = sp.some(destination)      

    # Private callback for `sendAllTokens`
    @sp.entry_point
    def sendAllTokens_callback(self, tokenBalance):
        sp.set_type(tokenBalance, sp.TNat)

        # Verify sender is the token contract
        sp.verify(sp.sender == self.data.tokenContractAddress, message = Errors.BAD_SENDER)

        # Verify state is correct.
        sp.verify(self.data.state == WAITING_FOR_TOKEN_BALANCE, message = Errors.BAD_STATE)

        # Unwrap saved parameters.
        destination = self.data.sendAllTokens_destination.open_some()

        # Invoke token contract
        tokenContractParam = sp.record(
            to_ = destination,
            from_ = sp.self_address,
            value = tokenBalance
        )
        contractHandle = sp.contract(
            sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
            self.data.tokenContractAddress,
            "transfer"
        ).open_some()
        sp.transfer(tokenContractParam, sp.mutez(0), contractHandle)

        # Reset state
        self.data.state = IDLE
        self.data.sendAllTokens_destination = sp.none      

    # Rescue FA1.2 Tokens
    @sp.entry_point
    def rescueFA12(self, params):
        sp.set_type(params, sp.TRecord(
            tokenContractAddress = sp.TAddress,
            amount = sp.TNat,
            destination = sp.TAddress,
        ).layout(("tokenContractAddress", ("amount", "destination"))))

        # Verify sender is governor.
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        # Transfer the tokens
        handle = sp.contract(
            sp.TRecord(
                from_ = sp.TAddress,
                to_ = sp.TAddress, 
                value = sp.TNat
            ).layout(("from_ as from", ("to_ as to", "value"))),
            params.tokenContractAddress,
            "transfer"
        ).open_some()
        arg = sp.record(from_ = sp.self_address, to_ = params.destination, value = params.amount)
        sp.transfer(arg, sp.mutez(0), handle)

    # Rescue FA2 tokens
    @sp.entry_point
    def rescueFA2(self, params):
        sp.set_type(params, sp.TRecord(
            tokenContractAddress = sp.TAddress,
            tokenId = sp.TNat,
            amount = sp.TNat,
            destination = sp.TAddress,
        ).layout(("tokenContractAddress", ("tokenId", ("amount", "destination")))))

        # Verify sender is governor.
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)

        # Transfer the tokens
        handle = sp.contract(
            sp.TList(
                sp.TRecord(
                    from_ = sp.TAddress,
                    txs = sp.TList(
                        sp.TRecord(
                            amount = sp.TNat,
                            to_ = sp.TAddress, 
                            token_id = sp.TNat,
                        ).layout(("to_", ("token_id", "amount")))
                    )
                ).layout(("from_", "txs"))
            ),
            params.tokenContractAddress,
            "transfer"
        ).open_some()

        arg = [
            sp.record(
            from_ = sp.self_address,
            txs = [
                sp.record(
                    amount = params.amount,
                    to_ = params.destination,
                    token_id = params.tokenId
                )
            ]
            )
        ]
        sp.transfer(arg, sp.mutez(0), handle)                

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
    FA12 = sp.io.import_script_from_url("file:./test-helpers/fa12.py")
    FA2 = sp.io.import_script_from_url("file:./test-helpers/fa2.py")
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

    @sp.add_test(name="send - succeeds when with less than the entire amount")
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

        # WHEN send is called with less than the full amount
        sendAmount = sp.mutez(2)
        param = (sendAmount, dummyContract.address)
        scenario += fund.send(param).run(
            sender = governorContractAddress,
        )

        # THEN the funds are sent.
        scenario.verify(fund.balance == (balance - sendAmount))
        scenario.verify(dummyContract.balance == sendAmount)        

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
            valid = False,
            exception = Errors.NOT_GOVERNOR
        )    

    ################################################################
    # sendAll
    ################################################################

    @sp.add_test(name="sendAll - succeeds when called by governor")
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

        # WHEN sendAll is called
        scenario += fund.sendAll(dummyContract.address).run(
            sender = governorContractAddress,
        )

        # THEN the funds are sent.
        scenario.verify(fund.balance == sp.mutez(0))
        scenario.verify(dummyContract.balance == balance)
     
    @sp.add_test(name="sendAll - fails when not called by governor")
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
        scenario += fund.sendAll(notGovernor).run(
            sender = notGovernor,
            valid = False,
            exception = Errors.NOT_GOVERNOR
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

    ################################################################
    # rescueFA2
    ################################################################

    @sp.add_test(name="rescueFA2 - rescues tokens")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an FA2 token contract
        config = FA2.FA2_config()
        token = FA2.FA2(
            config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),      
            admin = Addresses.TOKEN_ADMIN_ADDRESS
        )
        scenario += token

        # AND a dev fund contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # AND the dev fund has tokens given to it.
        value = sp.nat(100)
        tokenId = 0
        scenario += token.mint(    
            address = fund.address,
            amount = value,
            metadata = FA2.FA2.make_metadata(
                name = "SomeToken",
                decimals = 18,
                symbol= "ST"
            ),
            token_id = tokenId
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )
        
        # WHEN rescueFA2 is called.
        scenario += fund.rescueFA2(
            sp.record(
                destination = Addresses.ALICE_ADDRESS,
                amount = value,
                tokenId = tokenId,
                tokenContractAddress = token.address
            )
        ).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )    

        # THEN the tokens are rescued.
        scenario.verify(token.data.ledger[(fund.address, tokenId)].balance == sp.nat(0))
        scenario.verify(token.data.ledger[(Addresses.ALICE_ADDRESS, tokenId)].balance == value)

    @sp.add_test(name="rescueFA2 - fails if not called by govenror")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an FA2 token contract
        config = FA2.FA2_config()
        token = FA2.FA2(
            config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),      
            admin = Addresses.TOKEN_ADMIN_ADDRESS
        )
        scenario += token


        # AND a dev fund contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # AND the dev fund has tokens given to it.
        value = sp.nat(100)
        tokenId = 0
        scenario += token.mint(    
            address = fund.address,
            amount = value,
            metadata = FA2.FA2.make_metadata(
                name = "SomeToken",
                decimals = 18,
                symbol= "ST"
            ),
            token_id = tokenId
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )
        
        # WHEN rescueFA2 is called by someone other than the governor
        # THEN the call fails
        notGovernor = Addresses.NULL_ADDRESS
        scenario += fund.rescueFA2(
            sp.record(
                destination = Addresses.ALICE_ADDRESS,
                amount = value,
                tokenId = tokenId,
                tokenContractAddress = token.address
            )
        ).run(
            sender = notGovernor,
            valid = False,
            exception = Errors.NOT_GOVERNOR
        )    

    ################################################################
    # rescueFA12
    ################################################################

    @sp.add_test(name="rescueFA12 - rescues tokens")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an FA1.2 token contract
        token_metadata = {
            "decimals" : "18",
            "name" : "SomeToken",
            "symbol" : "ST",
        }
        contract_metadata = {
            "" : "tezos-storage:data",
        }
        token = FA12.FA12(
            admin = Addresses.TOKEN_ADMIN_ADDRESS,
            token_metadata = token_metadata,
            contract_metadata = contract_metadata,
            config = FA12.FA12_config(use_token_metadata_offchain_view = False)
        )
        scenario += token

        # AND a dev fund contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # AND the dev fund has tokens given to it.
        value = sp.nat(100)
        scenario += token.mint(
            sp.record(
                address = fund.address,
                value = value
            )
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )

        # WHEN rescueFA12 is called
        scenario += fund.rescueFA12(
            sp.record(
                destination = Addresses.ALICE_ADDRESS,
                amount = value,
                tokenContractAddress = token.address
            )
        ).run(
            sender = Addresses.GOVERNOR_ADDRESS,
        )    

        # THEN the tokens are rescued.
        scenario.verify(token.data.balances[fund.address].balance == sp.nat(0))
        scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == value)

    @sp.add_test(name="rescueFA12 - fails to rescue if not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN an FA1.2 token contract
        token_metadata = {
            "decimals" : "18",
            "name" : "SomeToken",
            "symbol" : "ST",
        }
        contract_metadata = {
            "" : "tezos-storage:data",
        }
        token = FA12.FA12(
            admin = Addresses.TOKEN_ADMIN_ADDRESS,
            token_metadata = token_metadata,
            contract_metadata = contract_metadata,
            config = FA12.FA12_config(use_token_metadata_offchain_view = False)
        )
        scenario += token

        # AND a dev fund contract
        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorContractAddress
        )
        scenario += fund

        # AND the dev fund has tokens given to it.
        value = sp.nat(100)
        scenario += token.mint(
            sp.record(
                address = fund.address,
                value = value
            )
        ).run(
            sender = Addresses.TOKEN_ADMIN_ADDRESS
        )

        # WHEN rescueFA12 is called by someone other than the governor.
        # THEN the call fails
        notGovernor = Addresses.NULL_ADDRESS
        scenario += fund.rescueFA12(
            sp.record(
                destination = Addresses.ALICE_ADDRESS,
                amount = value,
                tokenContractAddress = token.address
            )
        ).run(
            sender = notGovernor,
            valid = False,
            exception = Errors.NOT_GOVERNOR
        )    

    ################################################################
    # sendAllTokens
    ################################################################

    @sp.add_test(name="sendAllTokens - succeeds when called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract in the idle state
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract in the IDLE state
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = IDLE,
            sendAllTokens_destination = sp.none
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens is called
        destination = Addresses.ALICE_ADDRESS
        scenario += fund.sendAllTokens(destination).run(
            sender = governorAddress,
        )

        # THEN the fund is zero'ed
        scenario.verify(token.data.balances[fund.address].balance == 0)

        # AND the receiver was credited all of the tokens.
        scenario.verify(token.data.balances[destination].balance == fundTokens)

        # AND the state is reset
        scenario.verify(fund.data.state == IDLE)
        scenario.verify(fund.data.sendAllTokens_destination == sp.none)

    @sp.add_test(name="sendAllTokens - fails when not called by governor")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract in the idle state
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract in the IDLE state
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = IDLE,
            sendAllTokens_destination = sp.none
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens is called by someone other than the governor
        # THEN the call fails with NOT_GOVERNOR
        destination = Addresses.ALICE_ADDRESS
        notGovernor = Addresses.NULL_ADDRESS
        scenario += fund.sendAllTokens(destination).run(
            sender = notGovernor,

            valid = False,
            exception = Errors.NOT_GOVERNOR
        )

    @sp.add_test(name="sendAllTokens - fails in bad state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract in the idle state
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract in the WAITING_FOR_TOKEN_BALANCE state
        destination = Addresses.ALICE_ADDRESS
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = WAITING_FOR_TOKEN_BALANCE,
            sendAllTokens_destination = sp.some(destination)
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens is called
        # THEN the call fails with BAD_STATE
        scenario += fund.sendAllTokens(destination).run(
            sender = governorAddress,

            valid = False,
            exception = Errors.BAD_STATE
        ) 

    ################################################################
    # sendAllTokens_callback
    ################################################################

    @sp.add_test(name="sendAllTokens_callback - sends the token balance")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract that is waiting to send a balance to Alice
        recipientAddress = Addresses.ALICE_ADDRESS 
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = WAITING_FOR_TOKEN_BALANCE,
            sendAllTokens_destination = sp.some(recipientAddress)
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens_callback is called by the token contract
        scenario += fund.sendAllTokens_callback(fundTokens).run(
            sender = token.address,
        )

        # THEN the fund is zero'ed
        scenario.verify(token.data.balances[fund.address].balance == 0)

        # AND the recipient was credited the tokens.
        scenario.verify(token.data.balances[recipientAddress].balance == fundTokens)

        # AND the state is reset
        scenario.verify(fund.data.state == IDLE)
        scenario.verify(fund.data.sendAllTokens_destination == sp.none)

    @sp.add_test(name="sendAllTokens_callback - fails if sender is not the token contract")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract that is waiting to send a balance to Alice
        recipientAddress = Addresses.ALICE_ADDRESS 
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = WAITING_FOR_TOKEN_BALANCE,
            sendAllTokens_destination = sp.some(recipientAddress)
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens_callback is called by someone other than the token contract
        # THEN the call fails with BAD_SENDER
        notToken = Addresses.NULL_ADDRESS
        scenario += fund.sendAllTokens_callback(fundTokens).run(
            sender = notToken,

            valid = False,
            exception = Errors.BAD_SENDER
        )

    @sp.add_test(name="sendAllTokens_callback - fails in wrong state")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a Token contract.
        governorAddress = Addresses.GOVERNOR_ADDRESS
        token = Token.FA12(
            admin = governorAddress
        )
        scenario += token

        # AND a DevFund contract that is in the idle state
        recipientAddress = Addresses.ALICE_ADDRESS 
        fund = DevFundContract(
            governorContractAddress = governorAddress,
            tokenContractAddress = token.address,

            state = IDLE,
            sendAllTokens_destination = sp.none
        )
        scenario += fund

        # AND the fund has $1000 of tokens.
        fundTokens = 1000 * Constants.PRECISION 
        mintForFundParam = sp.record(address = fund.address, value = fundTokens)
        scenario += token.mint(mintForFundParam).run(
            sender = governorAddress
        )

        # WHEN sendAllTokens_callback is called by the token contract
        # THEN the call fails with BAD_STATE
        scenario += fund.sendAllTokens_callback(fundTokens).run(
            sender = token.address,

            valid = False,
            exception = Errors.BAD_STATE
        )          

    sp.add_compilation_target("dev-fund", DevFundContract())
