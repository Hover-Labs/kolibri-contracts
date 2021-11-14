# Fungible Assets - FA12
# Inspired by https://gitlab.com/tzip/tzip/blob/master/A/FA1.2.md

# This file is copied verbatim from http://smartpy.io/dev/?template=fa12.py on 12/18/2020.
# All changed lines are annotated with `CHANGED: <description>`

# Fungible Assets - FA12
# Inspired by https://gitlab.com/tzip/tzip/blob/master/A/FA1.2.md

import smartpy as sp

Addresses = sp.io.import_script_from_url("file:./test-helpers/addresses.py")

class FA12(sp.Contract):
    def __init__(
        self, 
        **extra_storage
    ):
        self.init(
            balances = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)), 
            totalSupply = 0, 
            **extra_storage
        )

    @sp.entry_point
    def transfer(self, params):
        sp.set_type(params, sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))))
        sp.verify(self.is_administrator(sp.sender) |
            (~self.is_paused() &
                ((params.from_ == sp.sender) |
                 (self.data.balances[params.from_].approvals[sp.sender] >= params.value))))

        # CHANGED: Add from_ address if needed.
        self.addAddressIfNecessary(params.from_)

        self.addAddressIfNecessary(params.to_)
        sp.verify(self.data.balances[params.from_].balance >= params.value)
        self.data.balances[params.from_].balance = sp.as_nat(self.data.balances[params.from_].balance - params.value)
        self.data.balances[params.to_].balance += params.value
        sp.if (params.from_ != sp.sender) & (~self.is_administrator(sp.sender)):
            self.data.balances[params.from_].approvals[sp.sender] = sp.as_nat(self.data.balances[params.from_].approvals[sp.sender] - params.value)

    @sp.entry_point
    def approve(self, params):
        sp.set_type(params, sp.TRecord(spender = sp.TAddress, value = sp.TNat).layout(("spender", "value")))

        # CHANGED: Add address if needed. This fixes a bug in our tests for checkpoints where you cannot approve
        # before you have a balance.
        self.addAddressIfNecessary(sp.sender)

        sp.verify(~self.is_paused())
        alreadyApproved = self.data.balances[sp.sender].approvals.get(params.spender, 0)
        sp.verify((alreadyApproved == 0) | (params.value == 0), "UnsafeAllowanceChange")
        self.data.balances[sp.sender].approvals[params.spender] = params.value

    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.balances.contains(address):
            self.data.balances[address] = sp.record(balance = 0, approvals = {})

    @sp.utils.view(sp.TNat)
    def getBalance(self, params):
        # CHANGED: Add address if needed. This fixes a bug in our tests where  you can't
        # get a balance when balance is implicitly zero.
        self.addAddressIfNecessary(params)

        sp.result(self.data.balances[params].balance)

    @sp.utils.view(sp.TNat)
    def getAllowance(self, params):
        # CHANGED: Add address if needed.
        self.addAddressIfNecessary(params.owner)

        # CHANGED: Default to zero.
        sp.result(self.data.balances[params.owner].approvals.get(params.spender, sp.nat(0)))

    @sp.utils.view(sp.TNat)
    def getTotalSupply(self, params):
        sp.set_type(params, sp.TUnit)
        sp.result(self.data.totalSupply)

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))

        # CHANGED: Allow sender to be this contract.
        sp.verify((self.is_administrator(sp.sender)) | (sp.sender == sp.self_address))

        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.value
        self.data.totalSupply += params.value

    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))

        # CHANGED: Allow sender to be this contract.
        sp.verify((self.is_administrator(sp.sender)) | (sp.sender == sp.self_address))

        sp.verify(self.data.balances[params.address].balance >= params.value)
        self.data.balances[params.address].balance = sp.as_nat(self.data.balances[params.address].balance - params.value)
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)

    # CHANGED: Hardcode this function to `False`. There is no administrator.
    def is_administrator(self, sender):
        return sp.bool(False)

    # CHANGED: Hardcode this function to `False`. The contract is not pausable.
    def is_paused(self):
        return sp.bool(False)

    # CHANGED: Remove `[get,set]Administrator` functions. There are no administrators. 
    # CHANGED: Remove `setPause`

if "templates" not in __name__:
    # @sp.add_test(name = "FA12")
    # def test():
    #     scenario = sp.test_scenario()
    #     scenario.h1("FA1.2 template - Fungible assets")

    #     scenario.table_of_contents()

    #     # sp.test_account generates ED25519 key-pairs deterministically:
    #     admin = sp.test_account("Administrator")
    #     alice = sp.test_account("Alice")
    #     bob   = sp.test_account("Robert")

    #     # Let's display the accounts:
    #     scenario.h1("Accounts")
    #     scenario.show([admin, alice, bob])

    #     scenario.h1("Contract")
    #     c1 = FA12(administratorAddress = admin.address)

    #     scenario.h1("Entry points")
    #     scenario += c1
    #     scenario.h2("Admin mints a few coins")
    #     # CHANGED: Run from c1 rather than admin since admin no longer exists.
    #     scenario += c1.mint(address = alice.address, value = 12).run(sender = c1.address)
    #     scenario += c1.mint(address = alice.address, value = 3).run(sender = c1.address)
    #     scenario += c1.mint(address = alice.address, value = 3).run(sender = c1.address)
    #     scenario.h2("Alice transfers to Bob")
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = alice)
    #     scenario.verify(c1.data.balances[alice.address].balance == 14)
    #     scenario.h2("Bob tries to transfer from Alice but he doesn't have her approval")
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob, valid = False)
    #     scenario.h2("Alice approves Bob and Bob transfers")
    #     scenario += c1.approve(spender = bob.address, value = 5).run(sender = alice)
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob)
    #     scenario.h2("Bob tries to over-transfer from Alice")
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = bob, valid = False)
    #     scenario.h2("Admin burns Bob token")
    #     # CHANGED: Run from c1 rather than admin since admin no longer exists.
    #     scenario += c1.burn(address = bob.address, value = 1).run(sender = c1.address)
    #     scenario.verify(c1.data.balances[alice.address].balance == 10)
    #     scenario.h2("Alice tries to burn Bob token")
    #     scenario += c1.burn(address = bob.address, value = 1).run(sender = alice, valid = False)
    #     # CHANGED: Remove test scenarios that deal with pause functionality.
    #     # scenario.h2("Admin pauses the contract and Alice cannot transfer anymore")
    #     # scenario += c1.setPause(True).run(sender = admin)
    #     # scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 4).run(sender = alice, valid = False)
    #     # scenario.verify(c1.data.balances[alice.address].balance == 10)
    #     # scenario.h2("Admin transfers while on pause")
        
    #     # CHANGED: Run from alice rather than admin since admin no longer exists.
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1).run(sender = alice)
        
    #     # CHANGED: Remove test scenarios that deal with pause functionality.
    #     # scenario.h2("Admin unpauses the contract and transferts are allowed")
    #     # scenario += c1.setPause(False).run(sender = admin)
    #     scenario.verify(c1.data.balances[alice.address].balance == 9)
    #     scenario += c1.transfer(from_ = alice.address, to_ = bob.address, value = 1).run(sender = alice)

    #     scenario.verify(c1.data.totalSupply == 17)
    #     scenario.verify(c1.data.balances[alice.address].balance == 8)
    #     scenario.verify(c1.data.balances[bob.address].balance == 9)

    sp.add_compilation_target("fa12", FA12())
