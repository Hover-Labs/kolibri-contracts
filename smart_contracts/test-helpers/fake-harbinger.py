import smartpy as sp

Constants = sp.io.import_script_from_url("file:common/constants.py")

# A contract which fakes a Harbinger oracle.
class FakeHarbingerContract(sp.Contract):
    def __init__(
      self, 
      harbingerValue = sp.nat(0),
      harbingerUpdateTime = sp.timestamp(0),
      harbingerAsset = Constants.ASSET_CODE
    ):
        self.init(
            harbingerValue = harbingerValue,
            harbingerUpdateTime = harbingerUpdateTime,
            harbingerAsset = harbingerAsset,
        )

    # Update the asset price.
    @sp.entry_point
    def setNewPrice(self, newValue):
        self.data.harbingerValue = newValue

    # Update - Not implemented
    @sp.entry_point
    def update(self):
        pass

    # Get - Returns the static value in the initializer
    @sp.entry_point
    def get(self, requestPair):
        sp.set_type(requestPair, sp.TPair(sp.TString, sp.TContract(Constants.HARBINGER_DATA_TYPE)))

        callback = sp.snd(requestPair)

        result = (self.data.harbingerAsset, (self.data.harbingerUpdateTime, self.data.harbingerValue))
        sp.transfer(result, sp.mutez(0), callback) 