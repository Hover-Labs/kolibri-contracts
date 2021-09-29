import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(lambdaResult = sp.none)

  @sp.entry_point
  def check(self, params):
    sp.set_type(params.params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))
    __s3 = sp.local("__s3", (sp.fst(params.params) * (1000000000000000000 + (sp.snd(sp.snd(params.params)) * sp.fst(sp.snd(params.params))))) // 1000000000000000000)
    sp.verify(__s3.value == params.result)

  @sp.entry_point
  def test(self, params):
    sp.set_type(params, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat)))
    __s4 = sp.local("__s4", (sp.fst(params) * (1000000000000000000 + (sp.snd(sp.snd(params)) * sp.fst(sp.snd(params))))) // 1000000000000000000)
    self.data.lambdaResult = sp.some(__s4.value)