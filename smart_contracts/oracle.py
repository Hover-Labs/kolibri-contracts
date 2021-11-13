import smartpy as sp

Addresses = sp.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.import_script_from_url("file:common/constants.py")
Errors = sp.import_script_from_url("file:common/errors.py")

################################################################
# State Machine
################################################################

IDLE = 0
WAITING_FOR_HARBINGER = 1

################################################################
# Contract
################################################################

# Contains an Oracle for an XTZ-USD price backed by Harbinger.
# See: https://github.com/tacoinfra/harbinger
class OracleContract(sp.Contract):
    # Initialize a new OracleContract contract.
    #
    # Parameters:
    #   harbingerContractAddress The address of the Harbinger contract. Defaults to the Coinbase Normalizer.
    def __init__(
        self, 
        state = IDLE,
        harbingerContractAddress = Addresses.HARBINGER_ADDRESS,
        maxDataDelaySec = sp.nat(60 * 30),
        governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    ):
        self.exception_optimization_level = "DefaultUnit"

        self.init(
            harbingerContractAddress = harbingerContractAddress,
            state = state,
            clientCallback = sp.none,
            maxDataDelaySec = maxDataDelaySec,
            governorContractAddress = governorContractAddress
        )

    ################################################################
    # Public Interface
    ################################################################

    # Disallow direct transfers.
    @sp.entry_point
    def default(self, param):
        sp.set_type(param, sp.TUnit)
        sp.failwith(Errors.CANNOT_RECEIVE_FUNDS)        

    # Retrieve the price of the XTZ-USD pair.
    #
    # Parameters:
    #   callback: A callback to call with the result. Parameter to callback is a single nat.
    @sp.entry_point
    def getXtzUsdRate(self, callback):
        sp.set_type(callback, sp.TContract(sp.TNat))

        # Can only be called from idle state
        sp.verify(self.data.state == IDLE, message = Errors.BAD_STATE)

        # Verify the call did not contain a balance.
        sp.verify(sp.amount == sp.mutez(0), message = Errors.AMOUNT_NOT_ALLOWED)

        # Set state to WAITING_FOR_HARBINGER
        self.data.state = WAITING_FOR_HARBINGER
        self.data.clientCallback = sp.some(sp.to_address(callback))

        # Callback to this contract.
        harbingerCallback = sp.self_entry_point(entry_point = 'getXtzUsdRate_callback')
        sp.set_type(harbingerCallback, sp.TContract(Constants.HARBINGER_DATA_TYPE))
        harbingerParam = (Constants.ASSET_CODE, harbingerCallback)

        harbingerHandle = sp.contract(
            sp.TPair(sp.TString, sp.TContract(Constants.HARBINGER_DATA_TYPE)),
            self.data.harbingerContractAddress,
            entry_point = "get"
        ).open_some()

        sp.transfer(harbingerParam, sp.mutez(0), harbingerHandle)

    ################################################################
    # Harbinger Callbacks
    ################################################################

    @sp.entry_point
    def getXtzUsdRate_callback(self, result):
        sp.set_type(result, Constants.HARBINGER_DATA_TYPE)

        # Can only be called from the WAITING_FOR_HARBINGER state.
        sp.verify(self.data.state == WAITING_FOR_HARBINGER, message = Errors.BAD_STATE)

        # Assert data came from Harbinger and is the correct asset.
        sp.verify(sp.sender == self.data.harbingerContractAddress, message = Errors.NOT_ORACLE)
        returnedAssetCode = sp.fst(result)
        sp.verify(returnedAssetCode == Constants.ASSET_CODE, message = Errors.WRONG_ASSET)

        # Assert data is recent.
        dataAge = sp.as_nat(sp.now - sp.fst(sp.snd(result)))
        sp.verify(dataAge < self.data.maxDataDelaySec, message = Errors.STALE_DATA)

        # Grab callback. Callback will always be `some` in the WAITING_FOR_HARBINGER state.
        clientCallback = self.data.clientCallback.open_some()
        clientCallback = sp.contract(
            sp.TNat, 
            clientCallback,
            ''
        ).open_some()

        clientCallbackParam = sp.snd(sp.snd(result)) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        
        # Call client callback
        sp.transfer(clientCallbackParam, sp.mutez(0), clientCallback)

        # Reset state.
        self.data.state = IDLE
        self.data.clientCallback = sp.none

    ################################################################
    # Governance
    ################################################################

    # Update the governor contract.
    @sp.entry_point
    def setGovernorContract(self, newGovernorContractAddress):
        sp.set_type(newGovernorContractAddress, sp.TAddress)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.governorContractAddress = newGovernorContractAddress

    # Update the max data delay.
    @sp.entry_point
    def setMaxDataDelaySec(self, newMaxDataDelaySec):
        sp.set_type(newMaxDataDelaySec, sp.TNat)

        sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
        self.data.maxDataDelaySec = newMaxDataDelaySec

# Only run tests if this file is main.
if __name__ == "__main__":

    ################################################################
    ################################################################
    # Tests
    ################################################################
    ################################################################

    DummyContract = sp.import_script_from_url("file:test-helpers/dummy-contract.py")
    FakeHarbinger = sp.import_script_from_url("file:test-helpers/fake-harbinger.py")

    ################################################################
    # getXtzUsdRate
    ################################################################

    @sp.add_test(name="getXtzUsdRate - fails when called from bad state")
    def test():
        # GIVEN an Oracle contract in the WAITING_FOR_HARBINGER state
        scenario = sp.test_scenario()

        oracle = OracleContract(
            state = WAITING_FOR_HARBINGER
        )
        scenario += oracle

        # AND a DummyContract to receive the retrieved value.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN a price is requested THEN the invocation fails.
        callback = sp.contract(sp.TNat, dummyContract.address, entry_point = "natCallback").open_some()
        scenario += oracle.getXtzUsdRate(callback).run(
            valid = False
        )

    @sp.add_test(name="getXtzUsdRate - fails when called with an amount")
    def test():
        # GIVEN an Oracle contract.
        scenario = sp.test_scenario()

        oracle = OracleContract(
        )
        scenario += oracle

        # AND a DummyContract to receive the retrieved value.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN a price is requested with an amount THEN the invocation fails.
        callback = sp.contract(sp.TNat, dummyContract.address, entry_point = "natCallback").open_some()
        scenario += oracle.getXtzUsdRate(callback).run(
            amount = sp.mutez(1),
            valid = False
        )

    @sp.add_test(name="getXtzUsdRate - retrieves correct value")
    def test():
        scenario = sp.test_scenario()

        # GIVEN a fake Harbinger contract.
        xtzUsdValue = 2310000 # $2.31
        harbinger = FakeHarbinger.FakeHarbingerContract(
            harbingerValue = xtzUsdValue,
            harbingerUpdateTime = sp.timestamp_from_utc_now(),
            harbingerAsset = Constants.ASSET_CODE
        )
        scenario += harbinger
        
        # AND an Oracle contract.    
        oracle = OracleContract(
            harbingerContractAddress = harbinger.address
        )
        scenario += oracle

        # AND a DummyContract to receive the retrieved value.
        dummyContract = DummyContract.DummyContract()
        scenario += dummyContract

        # WHEN a price is requested with an amount
        callback = sp.contract(sp.TNat, dummyContract.address, entry_point = "natCallback").open_some()
        scenario += oracle.getXtzUsdRate(callback).run(
            now = sp.timestamp_from_utc_now()
        )

        # THEN the dummy contract received the data, correctly converted to 10^-18 precision
        expectedValue = xtzUsdValue * Constants.MUTEZ_TO_KOLIBRI_CONVERSION
        scenario.verify(dummyContract.data.natValue == expectedValue)

        # AND the contract state is reset
        scenario.verify(oracle.data.state == IDLE)
        scenario.verify(oracle.data.clientCallback.is_some() == False)

    ################################################################
    # getXtzUsdRate_callback
    ################################################################

    @sp.add_test(name="getXtzUsdRate_callback - fails when called from bad state")
    def test():
        # GIVEN an Oracle contract in the IDLE state
        scenario = sp.test_scenario()

        harbingerAddress = Addresses.HARBINGER_ADDRESS
        oracle = OracleContract(
            harbingerContractAddress = harbingerAddress,
            state = IDLE
        )
        scenario += oracle

        # WHEN the callback is called THEN the call fails.
        harbingerResult = (Constants.ASSET_CODE, (sp.timestamp_from_utc_now(), 2310000))
        scenario += oracle.getXtzUsdRate_callback(harbingerResult).run(
            valid = False
        )

    @sp.add_test(name="getXtzUsdRate_callback - fails when not called from harbinger")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        harbingerAddress = Addresses.HARBINGER_ADDRESS
        oracle = OracleContract(
            harbingerContractAddress = harbingerAddress,
            state = WAITING_FOR_HARBINGER
        )
        scenario += oracle

        # WHEN the callback is called from someone other than Harbinger THEN the call fails.
        harbingerResult = (Constants.ASSET_CODE, (sp.timestamp_from_utc_now(), 2310000))
        notHarbinger = Addresses.NULL_ADDRESS
        scenario += oracle.getXtzUsdRate_callback(harbingerResult).run(
            sender = notHarbinger,
            valid = False
        )

    @sp.add_test(name="getXtzUsdRate_callback - fails when called with wrong asset")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        harbingerAddress = Addresses.HARBINGER_ADDRESS
        oracle = OracleContract(
            harbingerContractAddress = harbingerAddress,
            state = WAITING_FOR_HARBINGER
        )
        scenario += oracle

        # WHEN the callback contains data for an asset which is not XTZ-USD THEN the call fails.
        harbingerResult = ("BTC-USD", (sp.timestamp_from_utc_now(), 2310000))
        scenario += oracle.getXtzUsdRate_callback(harbingerResult).run(
            sender = harbingerAddress,
            valid = False
        )

    @sp.add_test(name="getXtzUsdRate_callback - fails when called with stale asset data")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        harbingerAddress = Addresses.HARBINGER_ADDRESS
        maxDataDelaySec = 30
        oracle = OracleContract(
            harbingerContractAddress = harbingerAddress,
            maxDataDelaySec =maxDataDelaySec,
            state = WAITING_FOR_HARBINGER
        )
        scenario += oracle

        # WHEN the callback is contains data at too old of a timestamp THEN the call fails
        nowSecs = 60
        now = sp.timestamp(nowSecs)
        staleDataTime = sp.timestamp(nowSecs - maxDataDelaySec - 1)

        harbingerResult = (Constants.ASSET_CODE, (staleDataTime, 2310000))
        scenario += oracle.getXtzUsdRate_callback(harbingerResult).run(
            sender = harbingerAddress,
            valid = False,
            now = now
        )    

    ################################################################
    # default
    ################################################################

    @sp.add_test(name="default - fails with calls to the default entrypoint")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        oracle = OracleContract()
        scenario += oracle

        # WHEN the default entry point is called THEN the request fails
        scenario += oracle.default(sp.unit).run(
            amount = sp.mutez(1),
            valid = False
        )

    ################################################################
    # setMaxDataDelaySec
    ################################################################

    @sp.add_test(name="setMaxDataDelaySec - succeeds when called by governor")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        oracle = OracleContract(
            governorContractAddress = governorContractAddress,
            maxDataDelaySec = 30,
        )
        scenario += oracle

        # WHEN the setMaxDataDelaySec is called with a new contract
        newMaxDataDelaySec = 60
        scenario += oracle.setMaxDataDelaySec(newMaxDataDelaySec).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(oracle.data.maxDataDelaySec == newMaxDataDelaySec)

    @sp.add_test(name="setMaxDataDelaySec - fails when not called by governor")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        oracle = OracleContract(
            governorContractAddress = governorContractAddress
        )
        scenario += oracle

        # WHEN the setMaxDataDelaySec is called by someone who isn't the governor THEN the call fails
        newMaxDataDelaySec = 60
        scenario += oracle.setMaxDataDelaySec(newMaxDataDelaySec).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    ################################################################
    # setGovernorContract
    ################################################################

    @sp.add_test(name="setGovernorContract - succeeds when called by governor")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        oracle = OracleContract(
            governorContractAddress = governorContractAddress
        )
        scenario += oracle

        # WHEN the setGovernorContract is called with a new contract
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += oracle.setGovernorContract(rotatedAddress).run(
            sender = governorContractAddress,
        )

        # THEN the contract is updated.
        scenario.verify(oracle.data.governorContractAddress == rotatedAddress)

    @sp.add_test(name="setGovernorContract - fails when not called by governor")
    def test():
        # GIVEN an Oracle contract
        scenario = sp.test_scenario()

        governorContractAddress = Addresses.GOVERNOR_ADDRESS
        oracle = OracleContract(
            governorContractAddress = governorContractAddress
        )
        scenario += oracle

        # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
        rotatedAddress = Addresses.ROTATED_ADDRESS
        scenario += oracle.setGovernorContract(rotatedAddress).run(
            sender = Addresses.NULL_ADDRESS,
            valid = False
        )    

    sp.add_compilation_target("oracle", OracleContract())
