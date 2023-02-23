import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(intValue = sp.TInt, natValue = sp.TNat).layout(("intValue", "natValue")))
    self.init(intValue = 0,
              natValue = 0)

  @sp.entry_point
  def default(self):
    pass

  @sp.entry_point
  def intCallback(self, params):
    self.data.intValue = params

  @sp.entry_point
  def natCallback(self, params):
    self.data.natValue = params

sp.add_compilation_target("test", Contract())