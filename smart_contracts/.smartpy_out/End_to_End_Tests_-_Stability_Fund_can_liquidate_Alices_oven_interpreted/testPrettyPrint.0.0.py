import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(harbingerAsset = 'XTZ-USD', harbingerUpdateTime = sp.timestamp(0), harbingerValue = 2000000)

  @sp.entry_point
  def get(self, params):
    sp.set_type(params, sp.TPair(sp.TString, sp.TContract(sp.TPair(sp.TString, sp.TPair(sp.TTimestamp, sp.TNat)))))
    sp.transfer((self.data.harbingerAsset, (self.data.harbingerUpdateTime, self.data.harbingerValue)), sp.tez(0), sp.snd(params))

  @sp.entry_point
  def setNewPrice(self, params):
    self.data.harbingerValue = params

  @sp.entry_point
  def update(self, params):
    pass