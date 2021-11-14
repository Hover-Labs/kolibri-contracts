# Fungible Assets - FA12
# Inspired by https://gitlab.com/tzip/tzip/blob/master/A/FA1.2.md

# This file is copied verbatim from http://smartpy.io/dev/?template=fa12.py on 11/02/2020.
# All changed lines are annotated with `CHANGED: <description>`

import smartpy as sp

# CHANGED: Import errors.
Errors = sp.io.import_script_from_url("file:common/errors.py")

# CHANGED: Import address helpers
Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")

# CHANGED: Define a constant for the empty string in the metadata bigmap
METADATA_KEY = ""

class FA12_core(sp.Contract):
    def __init__(self, **extra_storage):
        token_id = sp.nat(0)

        kusd_metadata = sp.map(
            l = {
                "name": sp.bytes('0x4b6f6c6962726920555344'), # Kolibri USD
                "decimals": sp.bytes('0x3138'), # 18
                "symbol": sp.bytes('0x6b555344'), # kUSD
                "icon": sp.bytes('0x2068747470733a2f2f6b6f6c696272692d646174612e73332e616d617a6f6e6177732e636f6d2f6c6f676f2e706e67') # https://kolibri-data.s3.amazonaws.com/logo.png
            },
            tkey = sp.TString,
            tvalue = sp.TBytes
        )
        kusd_entry = (token_id, kusd_metadata)
        token_metadata = sp.big_map(
            l = {
                token_id: kusd_entry,
            },
            tkey = sp.TNat,
            tvalue = sp.TPair(sp.TNat, sp.TMap(sp.TString, sp.TBytes))
        )
        
        # Hexadecimal representation of:
        # { name: " Kolibri Token Contract", "description": "FA1.2 Implementation of kUSD", "author": "Hover Labs", "homepage":  "https://kolibri.finance", "interfaces": [ "TZIP-007-2021-01-29"] }
        metadata_data = sp.bytes('0x7b206e616d653a2022204b6f6c6962726920546f6b656e20436f6e7472616374222c20226465736372697074696f6e223a20224641312e3220496d706c656d656e746174696f6e206f66206b555344222c2022617574686f72223a2022486f766572204c616273222c2022686f6d6570616765223a20202268747470733a2f2f6b6f6c696272692e66696e616e6365222c2022696e7465726661636573223a205b2022545a49502d3030372d323032312d30312d3239225d207d')

        metadata = sp.big_map(
            l = {
                "": sp.bytes('0x74657a6f732d73746f726167653a64617461'), # "tezos-storage:data"
                "data": metadata_data
            },
            tkey = sp.TString,
            tvalue = sp.TBytes            
        )

        self.exception_optimization_level = "DefaultUnit"

        self.init(
            balances = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)), 
            totalSupply = 0, 
            # CHANGED: Include metadata and token_metadata bigmap in storage.
            metadata = metadata,
            token_metadata = token_metadata,
            **extra_storage
        )

    @sp.entry_point
    def transfer(self, params):
        sp.set_type(params, sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))))
        sp.verify(self.is_administrator(sp.sender) |
            (~self.is_paused() &
                ((params.from_ == sp.sender) |
                 (self.data.balances[params.from_].approvals[sp.sender] >= params.value))), Errors.TOKEN_NO_TRANSFER_PERMISSION)
        self.addAddressIfNecessary(params.to_)
        sp.verify(self.data.balances[params.from_].balance >= params.value, Errors.TOKEN_INSUFFICIENT_BALANCE)
        self.data.balances[params.from_].balance = sp.as_nat(self.data.balances[params.from_].balance - params.value)
        self.data.balances[params.to_].balance += params.value
        sp.if (params.from_ != sp.sender) & (~self.is_administrator(sp.sender)):
            self.data.balances[params.from_].approvals[sp.sender] = sp.as_nat(self.data.balances[params.from_].approvals[sp.sender] - params.value)

    @sp.entry_point
    def approve(self, params):
        sp.set_type(params, sp.TRecord(spender = sp.TAddress, value = sp.TNat).layout(("spender", "value")))
        sp.verify(~self.is_paused())
        alreadyApproved = self.data.balances[sp.sender].approvals.get(params.spender, 0)
        sp.verify((alreadyApproved == 0) | (params.value == 0), Errors.TOKEN_UNSAFE_ALLOWANCE_CHANGE)
        self.data.balances[sp.sender].approvals[params.spender] = params.value

    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.balances.contains(address):
            self.data.balances[address] = sp.record(balance = 0, approvals = {})

    @sp.utils.view(sp.TNat)
    def getBalance(self, params):
        sp.result(self.data.balances[params].balance)

    @sp.utils.view(sp.TNat)
    def getAllowance(self, params):
        sp.result(self.data.balances[params.owner].approvals[params.spender])

    @sp.utils.view(sp.TNat)
    def getTotalSupply(self, params):
        sp.set_type(params, sp.TUnit)
        sp.result(self.data.totalSupply)

    # this is not part of the standard but can be supported through inheritance.
    def is_paused(self):
        return sp.bool(False)

    # this is not part of the standard but can be supported through inheritance.
    def is_administrator(self, sender):
        return sp.bool(False)

class FA12_mint_burn(FA12_core):
    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(self.is_administrator(sp.sender), Errors.TOKEN_NOT_ADMINISTRATOR)
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

        # CHANGED: Verify that the debt ceiling is not passed.
        sp.verify(self.data.totalSupply <= self.data.debtCeiling, Errors.DEBT_CEILING)

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(self.is_administrator(sp.sender), Errors.TOKEN_NOT_ADMINISTRATOR)
        sp.verify(self.data.balances[params.address].balance >= params.value, Errors.TOKEN_INSUFFICIENT_BALANCE)
        self.data.balances[params.address].balance = sp.as_nat(self.data.balances[params.address].balance - params.value)
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)

class FA12_administrator(FA12_core):
    def is_administrator(self, sender):
        return sender == self.data.administrator

    @sp.entry_point
    def setAdministrator(self, params):
        sp.set_type(params, sp.TAddress)

        # CHANGED: Allow the governor to set the administrator, instead of the administrator.
        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.administrator = params

    @sp.utils.view(sp.TAddress)
    def getAdministrator(self, params):
        sp.set_type(params, sp.TUnit)
        sp.result(self.data.administrator)

class FA12_pause(FA12_core):
    def is_paused(self):
        return self.data.paused

    @sp.entry_point
    def setPause(self, params):
        sp.set_type(params, sp.TBool)
        sp.verify(self.is_administrator(sp.sender), Errors.TOKEN_NOT_ADMINISTRATOR)
        self.data.paused = params

class FA12(FA12_mint_burn, FA12_administrator, FA12_pause, FA12_core):
    def __init__(
        self, 
        # CHANGED: Assign a default value to `admin`
        admin = Addresses.GOVERNOR_ADDRESS,

        # CHANGED: Add a governor contract.
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,

        # CHANGED: Add a debt ceiling
        debtCeiling = sp.nat(1000000000000000000000000000000000000000000000000000000000000000000000000)
    ):
        FA12_core.__init__(
            self, 
            paused = False, 
            administrator = admin, 
            governorContractAddress = governorContractAddress,
            debtCeiling = debtCeiling
        )  

    # CHANGED: Add entrypoint to update governor.
    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # CHANGED: Add entrypoint to set debt ceiling.
    @sp.entry_point
    def setDebtCeiling(self, newDebtCeiling):
        sp.set_type(newDebtCeiling, sp.TNat)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.debtCeiling = newDebtCeiling

    # CHANGED: Allow governor to update contract metadata.	
    @sp.entry_point	
    def updateContractMetadata(self, params):	
        sp.set_type(params, sp.TPair(sp.TString, sp.TBytes))	

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        key = sp.fst(params)	
        value = sp.snd(params)	
        self.data.metadata[key] = value

    # CHANGED: Allow governor to update token metadata.	
    @sp.entry_point	
    def updateTokenMetadata(self, params):	
        sp.set_type(params, sp.TPair(sp.TNat, sp.TMap(sp.TString, sp.TBytes)))	

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.token_metadata[0] = params

class Viewer(sp.Contract):
    def __init__(self, t):
        self.init(last = sp.none)
        self.init_type(sp.TRecord(last = sp.TOption(t)))
    @sp.entry_point
    def target(self, params):
        self.data.last = sp.some(params)

# Only run tests if this file is main.
if __name__ == "__main__":

    # if "templates" not in __name__:
    #     @sp.add_test(name = "FA12")
    #     def test():

    #         scenario = sp.test_scenario()
    #         scenario.h1("FA1.2 template - Fungible assets")

    #         scenario.table_of_contents()

    #         # sp.test_account generates ED25519 key-pairs deterministically:
    #         admin = sp.test_account("Administrator")
    #         alice = sp.test_account("Alice")
    #         bob   = sp.test_account("Robert")

    #         # Let's display the accounts:
    #         scenario.h1("Accounts")
    #         scenario.show([admin, alice, bob])

    #         scenario.h1("Contract")
    #         c1 = FA12(admin.address)

    #         scenario.h1("Entry points")
    #         scenario += c1
    #         scenario.h2("Admin mints a few coins")
    #         scenario += c1.mint(address = alice.address, value = 12).run(sender = admin)
    #         scenario += c1.mint(address = alice.address, value = 3).run(sender = admin)
    #         scenario += c1.mint(address = alice.address, value = 3).run(sender = admin)
    #         scenario.h2("Alice transfers to Bob")
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = alice)
    #         scenario.verify(c1.data.balances[alice.address].balance == 14)
    #         scenario.h2("Bob tries to transfer from Alice but he doesn't have her approval")
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob, valid = False)
    #         scenario.h2("Alice approves Bob and Bob transfers")
    #         scenario += c1.approve(spender = bob.address, value = 5).run(sender = alice)
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob)
    #         scenario.h2("Bob tries to over-transfer from Alice")
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob, valid = False)
    #         scenario.h2("Admin burns Bob token")
    #         scenario += c1.burn(address = bob.address, value = 1).run(sender = admin)
    #         scenario.verify(c1.data.balances[alice.address].balance == 10)
    #         scenario.h2("Alice tries to burn Bob token")
    #         scenario += c1.burn(address = bob.address, value = 1).run(sender = alice, valid = False)
    #         scenario.h2("Admin pauses the contract and Alice cannot transfer anymore")
    #         scenario += c1.setPause(True).run(sender = admin)
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = alice, valid = False)
    #         scenario.verify(c1.data.balances[alice.address].balance == 10)
    #         scenario.h2("Admin transfers while on pause")
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1).run(sender = admin)
    #         scenario.h2("Admin unpauses the contract and transfers are allowed")
    #         scenario += c1.setPause(False).run(sender = admin)
    #         scenario.verify(c1.data.balances[alice.address].balance == 9)
    #         scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1).run(sender = alice)

    #         scenario.verify(c1.data.totalSupply == 17)
    #         scenario.verify(c1.data.balances[alice.address].balance == 8)
    #         scenario.verify(c1.data.balances[bob.address].balance == 9)

    #         scenario.h1("Views")
    #         scenario.h2("Balance")
    #         view_balance = Viewer(sp.TNat)
    #         scenario += view_balance
    #         scenario += c1.getBalance((alice.address, view_balance.typed))
    #         scenario.verify_equal(view_balance.data.last, sp.some(8))

    #         scenario.h2("Administrator")
    #         view_administrator = Viewer(sp.TAddress)
    #         scenario += view_administrator
    #         scenario += c1.getAdministrator((sp.unit, view_administrator.typed))
    #         scenario.verify_equal(view_administrator.data.last, sp.some(admin.address))

    #         scenario.h2("Total Supply")
    #         view_totalSupply = Viewer(sp.TNat)
    #         scenario += view_totalSupply
    #         scenario += c1.getTotalSupply((sp.unit, view_totalSupply.typed))
    #         scenario.verify_equal(view_totalSupply.data.last, sp.some(17))

    #         scenario.h2("Allowance")
    #         view_allowance = Viewer(sp.TNat)
    #         scenario += view_allowance
    #         scenario += c1.getAllowance((sp.record(owner = alice.address, spender = bob.address), view_allowance.typed))
    #         scenario.verify_equal(view_allowance.data.last, sp.some(1))
    
    # # CHANGED: Additional tests added below this line.

    # ################################################################
    # # mint
    # ################################################################

    # Dummy = sp.io.import_script_from_url("file:test-helpers/dummy-contract.py")

    # @sp.add_test(name="mint - respects debt ceiling")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     debtCeiling = 100
    #     token = FA12(
    #         admin = Addresses.GOVERNOR_ADDRESS,
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #         debtCeiling = debtCeiling
    #     )
    #     scenario += token

    #     # AND a token holder.
    #     tokenHolder = Dummy.DummyContract()
    #     scenario += tokenHolder

    #     # WHEN tokens are minted to the debt ceiling.
    #     mintParam = sp.record(address= tokenHolder.address, value= debtCeiling)
    #     scenario += token.mint(mintParam).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN tokens are minted successfully
    #     scenario.verify(token.data.balances[tokenHolder.address].balance == debtCeiling)
    #     scenario.verify(token.data.totalSupply == debtCeiling)

    #     # WHEN another mint is called THEN the call fails
    #     mintParam = sp.record(address= tokenHolder.address, value= 1)
    #     scenario += token.mint(mintParam).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #         valid = False
    #     )

    # ################################################################
    # # setDebtCeiling
    # ################################################################

    # @sp.add_test(name="setDebtCeiling - succeeds when called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #         debtCeiling = 123
    #     )
    #     scenario += token

    #     # WHEN the setDebtCeiling is called with a new ceiling
    #     newDebtCeiling = 456
    #     scenario += token.setDebtCeiling(newDebtCeiling).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN the contract is updated.
    #     scenario.verify(token.data.debtCeiling == newDebtCeiling)

    # @sp.add_test(name="setDebtCeiling - fails when not called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #         debtCeiling = 123
    #     )
    #     scenario += token

    #     # WHEN the setDebtCeiling is called by someone who isn't the governor THEN the call fails
    #     newDebtCeiling = 456
    #     scenario += token.setDebtCeiling(newDebtCeiling).run(
    #         sender = Addresses.NULL_ADDRESS,
    #         valid = False
    #     )    

    # ################################################################
    # # updateContractMetadata
    # ################################################################

    # @sp.add_test(name="updateContractMetadata - succeeds when called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #     )
    #     scenario += token

    #     # WHEN the updateContractMetadata is called with a new locator
    #     locatorKey = ""
    #     newLocator = sp.bytes('0x1234567890')
    #     scenario += token.updateContractMetadata((locatorKey, newLocator)).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN the contract is updated.
    #     scenario.verify(token.data.metadata[locatorKey] == newLocator)

    # @sp.add_test(name="updateContractMetadata - fails when not called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #     )
    #     scenario += token

    #     # WHEN the updateContractMetadata is called by someone who isn't the governor THEN the call fails
    #     locatorKey = ""
    #     newLocator = sp.bytes('0x1234567890')
    #     scenario += token.updateContractMetadata((locatorKey, newLocator)).run(
    #         sender = Addresses.NULL_ADDRESS,
    #         valid = False
    #     )            

    # ################################################################
    # # updateTokenMetadata
    # ################################################################

    # @sp.add_test(name="updateTokenMetadata - succeeds when called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #     )
    #     scenario += token

    #     # WHEN the updateTokenMetadata is called with a new data set.
    #     newKey = "new"
    #     newValue = sp.bytes('0x123456')
    #     newMap = sp.map(
    #         l = {
    #             newKey: newValue
    #         },
    #         tkey = sp.TString,
    #         tvalue = sp.TBytes
    #     )
    #     newData = (sp.nat(0), newMap)

    #     scenario += token.updateTokenMetadata(newData).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN the contract is updated.
    #     tokenMetadata = token.data.token_metadata[0]
    #     tokenId = sp.fst(tokenMetadata)
    #     tokenMetadataMap = sp.snd(tokenMetadata)
                
    #     scenario.verify(tokenId == sp.nat(0))
    #     scenario.verify(tokenMetadataMap[newKey] == newValue)

    # @sp.add_test(name="updateTokenMetadata - fails when not called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    #     )
    #     scenario += token

    #     # WHEN the updateTokenMetadata is called by someone who isn't the governor THEN the call fails
    #     newMap = sp.map(
    #         l = {
    #             "new": sp.bytes('0x123456')
    #         },
    #         tkey = sp.TString,
    #         tvalue = sp.TBytes
    #     )
    #     newData = (sp.nat(0), newMap)
    #     scenario += token.updateTokenMetadata(newData).run(
    #         sender = Addresses.NULL_ADDRESS,
    #         valid = False
    #     )            

    # ################################################################
    # # setAdministrator
    # ################################################################

    # @sp.add_test(name="setAdministrator - succeeds when called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         admin = Addresses.FUND_ADMINISTRATOR_ADDRESS,
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS
    #     )
    #     scenario += token

    #     # WHEN the setAdministrator is called with a new contract
    #     scenario += token.setAdministrator(Addresses.ROTATED_ADDRESS).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN the contract is updated.
    #     scenario.verify(token.data.administrator == Addresses.ROTATED_ADDRESS)

    # @sp.add_test(name="setAdministrator - fails when not called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         admin = Addresses.FUND_ADMINISTRATOR_ADDRESS,
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS
    #     )
    #     scenario += token

    #     # WHEN the setAdministrator is called by someone who isn't the governor THEN the call fails
    #     scenario += token.setAdministrator(Addresses.ROTATED_ADDRESS).run(
    #         sender = Addresses.NULL_ADDRESS,
    #         valid = False
    #     )    


    # ################################################################
    # # setGovernorContract
    # ################################################################

    # @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS
    #     )
    #     scenario += token

    #     # WHEN the setGovernorContract is called with a new contract
    #     scenario += token.setGovernorContract(Addresses.ROTATED_ADDRESS).run(
    #         sender = Addresses.GOVERNOR_ADDRESS,
    #     )

    #     # THEN the contract is updated.
    #     scenario.verify(token.data.governorContractAddress == Addresses.ROTATED_ADDRESS)

    # @sp.add_test(name="setGovernorContract - fails when not called by governor")
    # def test():
    #     # GIVEN a Token contract
    #     scenario = sp.test_scenario()

    #     token = FA12(
    #         governorContractAddress = Addresses.GOVERNOR_ADDRESS
    #     )
    #     scenario += token

    #     # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
    #     scenario += token.setGovernorContract(Addresses.ROTATED_ADDRESS).run(
    #         sender = Addresses.NULL_ADDRESS,
    #         valid = False
    #     )    

    sp.add_compilation_target("token", FA12())
