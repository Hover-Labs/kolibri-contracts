import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init()

  @sp.entry_point
  def default(self, params):
    pass

  @sp.entry_point
  def liquidate(self, params):
    sp.set_type(params, sp.TAddress)
    sp.send(params, sp.tez(0))