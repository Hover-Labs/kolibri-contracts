import smartpy as sp

# A fake liquidity pool which does not exchange received XTZ for kUSD
class FakeLiquidityPoolContract(sp.Contract):
    def __init__(
      self, 
    ):
        self.init(
        )

    # Accept and do nothing with any XTZ sent.
    @sp.entry_point
    def default(self, param):
        pass        

    # Liquidate an oven.
    @sp.entry_point
    def liquidate(self, targetOven):
        sp.set_type(targetOven, sp.TAddress)

        contractHandle = sp.contract(
            sp.TUnit,
            targetOven,
            "liquidate"
        ).open_some()
        sp.transfer(sp.unit, sp.mutez(0), contractHandle)
