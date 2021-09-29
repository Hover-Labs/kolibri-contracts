import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init(lambdaResult = sp.none)

  @sp.entry_point
  def check(self, params):
    sp.set_type(params.params, sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))
    __s1 = sp.local("__s1", sp.as_nat(sp.fst(sp.ediv(sp.fst(sp.ediv(sp.snd(sp.snd(sp.snd(params.params))) * 1000000000000000000, sp.as_nat(sp.fst(params.params))).open_some()) * (sp.fst(sp.snd(params.params)) + sp.fst(sp.snd(sp.snd(params.params)))), 1000000000000000000).open_some()) - (sp.fst(sp.snd(params.params)) + sp.fst(sp.snd(sp.snd(params.params))))))
    sp.verify(__s1.value == params.result)

  @sp.entry_point
  def test(self, params):
    sp.set_type(params, sp.TPair(sp.TInt, sp.TPair(sp.TNat, sp.TPair(sp.TNat, sp.TNat))))
    __s2 = sp.local("__s2", sp.as_nat(sp.fst(sp.ediv(sp.fst(sp.ediv(sp.snd(sp.snd(sp.snd(params))) * 1000000000000000000, sp.as_nat(sp.fst(params))).open_some()) * (sp.fst(sp.snd(params)) + sp.fst(sp.snd(sp.snd(params)))), 1000000000000000000).open_some()) - (sp.fst(sp.snd(params)) + sp.fst(sp.snd(sp.snd(params))))))
    self.data.lambdaResult = sp.some(__s2.value)