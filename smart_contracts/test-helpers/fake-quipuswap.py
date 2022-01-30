import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")

# A contract which acts like a quipuswap pool. 
# Parameters are captured for inspection.
class FakeQuipuswapContract(sp.Contract):
    def __init__(
      self, 
    ):
        self.init(
            amountOut = sp.nat(0),
            destination = Addresses.NULL_ADDRESS,
        )

    # Update - Not implemented
    @sp.entry_point
    def update(self):
        pass

    # Fake entrypoint to make a trade. captures parameters for inspection.
    @sp.entry_point
    def tezToTokenPayment(self, requestPair):
        sp.set_type(requestPair,  sp.TPair(sp.TNat, sp.TAddress))

        self.data.amountOut = sp.fst(requestPair)
        self.data.destination = sp.snd(requestPair)

