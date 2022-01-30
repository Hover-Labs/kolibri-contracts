import smartpy as sp

Addresses = sp.io.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.io.import_script_from_url("file:common/constants.py")
Errors = sp.io.import_script_from_url("file:common/errors.py")

################################################################
# Contract
################################################################

class QuipuswapProxyContract(sp.Contract):
  def __init__(
    self, 
    governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    harbingerContractAddress = Addresses.HARBINGER_ADDRESS,
    liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS,
    pauseGuardianContractAddress = Addresses.PAUSE_GUARDIAN_ADDRESS,
    quipuswapContractAddress = Addresses.QUIPUSWAP_ADDRESS,

    paused = False,

    maxDataDelaySec = sp.nat(60 * 30),
    slippageTolerance = sp.nat(0),
  ):
    self.init(
      governorContractAddress = governorContractAddress,
      harbingerContractAddress = harbingerContractAddress,
      liquidityPoolContractAddress = liquidityPoolContractAddress,
      pauseGuardianContractAddress = pauseGuardianContractAddress,
      quipuswapContractAddress = quipuswapContractAddress,

      paused = paused,

      maxDataDelaySec = maxDataDelaySec,
      slippageTolerance = slippageTolerance,
    )

  ################################################################
  # Trade API
  ################################################################

  @sp.entry_point
  def tezToTokenPayment(self, param):
    sp.set_type(param, sp.TPair(sp.TNat, sp.TAddress))

    # Verify that the sender is the Liquidity Pool
    sp.verify(sp.sender == self.data.liquidityPoolContractAddress, Errors.BAD_SENDER)
    
    # Verify the contract isn't paused.
    sp.verify(self.data.paused == False, Errors.PAUSED)

    # Read a price from Harbinger
    harbingerData = sp.view(
      "getPrice",
      self.data.harbingerContractAddress,
      Constants.ASSET_CODE,
      sp.TPair(sp.TTimestamp, sp.TNat)
    ).open_some()

    # Assert that the Harbinger data is recent
    dataAge = sp.as_nat(sp.now - sp.fst(harbingerData))
    sp.verify(dataAge < self.data.maxDataDelaySec, Errors.STALE_DATA)
  
    # Upsample all numbers to have 18 digits of precision
    harbingerPrice = (sp.snd(harbingerData) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION)
    xtzToTrade = sp.utils.mutez_to_nat(sp.amount) * Constants.MUTEZ_TO_KOLIBRI_CONVERSION

    # Calculate the expected kUSD with no slippage.
    # Expected out with no slippage = (Price of XTZ / USD) * (number of XTZ to trade)
    optimalOut = (harbingerPrice * xtzToTrade) // Constants.PRECISION

    # Apply slippage tolerance
    # Expected out with slippage = (optimal out from above) * (1 - slippage tolerance)
    percent = sp.as_nat(100 - self.data.slippageTolerance)
    requiredOut = (optimalOut * percent) // 100 # Note that percent is specified in scale = 100

    # Invoke a quipuswap trade
    tradeParam = (
      requiredOut,
      self.data.liquidityPoolContractAddress,
    )
    tradeHandle = sp.contract(
      sp.TPair(sp.TNat, sp.TAddress),
      self.data.quipuswapContractAddress,
      "tezToTokenPayment"
    ).open_some()
    sp.transfer(tradeParam, sp.amount, tradeHandle)

  ################################################################
  # Pause Guardian
  ################################################################

  # Pause the system
  @sp.entry_point
  def pause(self):
    sp.verify(sp.sender == self.data.pauseGuardianContractAddress, message = Errors.NOT_PAUSE_GUARDIAN)
    self.data.paused = True

  ################################################################
  # Governance
  ################################################################

  # Update the max data delay.
  @sp.entry_point
  def setMaxDataDelaySec(self, newMaxDataDelaySec):
    sp.set_type(newMaxDataDelaySec, sp.TNat)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.maxDataDelaySec = newMaxDataDelaySec

  # Set slippage tolerance
  @sp.entry_point
  def setSlippageTolerance(self, newSlippageTolerance):
    sp.set_type(newSlippageTolerance, sp.TNat)
    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.slippageTolerance = newSlippageTolerance

  # Unpause the system.
  @sp.entry_point
  def unpause(self):
    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.paused = False

  # Update the LiquidityPool contract.
  @sp.entry_point
  def setLiquidityPoolContract(self, newLiquidityPoolContractAddress):
    sp.set_type(newLiquidityPoolContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.liquidityPoolContractAddress = newLiquidityPoolContractAddress

  # Update the Harbinger contract.
  @sp.entry_point
  def setHarbingerContract(self, newHarbingerContractAddress):
    sp.set_type(newHarbingerContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.harbingerContractAddress = newHarbingerContractAddress

  # Update the pause guardian contract.
  @sp.entry_point
  def setPauseGuardianContract(self, newPauseGuardianContractAddress):
    sp.set_type(newPauseGuardianContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.pauseGuardianContractAddress = newPauseGuardianContractAddress

  # Update the Quipuswap contract.
  @sp.entry_point
  def setQuipuswapContract(self, newQuipuswapContractAddress):
    sp.set_type(newQuipuswapContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.quipuswapContractAddress = newQuipuswapContractAddress

  # Update the governor contract.
  @sp.entry_point
  def setGovernorContract(self, newGovernorContractAddress):
    sp.set_type(newGovernorContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.governorContractAddress = newGovernorContractAddress

# Only run tests if this file is main.
if __name__ == "__main__":

  ################################################################
  ################################################################
  # Tests
  ################################################################
  ################################################################

  FakeHarbinger = sp.io.import_script_from_url("file:test-helpers/fake-harbinger.py")
  FakeQuipuswap = sp.io.import_script_from_url("file:test-helpers/fake-quipuswap.py")

  
#     # Calculate the expected kUSD with no slippage.
#     # Expected out with no slippage = (Price of XTZ / USD) * (number of XTZ to trade)
#     optimalOut = (harbingerPrice * xtzToTrade) // Constants.PRECISION

#     # Apply slippage tolerance
#     # Expected out with slippage = (optimal out from above) * (1 - slippage tolerance)
#     percent = sp.as_nat(100 - self.data.slippageTolerance)
#     requiredOut = (optimalOut * percent) // 100 # Note that percent is specified in scale = 100

#     # Invoke a quipuswap trade
#     tradeParam = (
#       requiredOut,
#       self.data.liquidityPoolContractAddress,
#     )
#     tradeHandle = sp.contract(
#       sp.TPair(sp.TNat, sp.TAddress),
#       self.data.quipuswapContractAddress,
#       "tezToTokenPayment"
#     ).open_some()
#     sp.transfer(tradeParam, sp.amount, tradeHandle)


  ################################################################
  # tezToTokenPayment
  ################################################################


  @sp.add_test(name="tezToTokenPayment - correctly calculates amount out with 20 percent slippage")
  def test():
    scenario = sp.test_scenario()
    
    # GIVEN a moment in time.
    currentTime = sp.timestamp(1000)
    
    # AND fake harbinger contract
    harbinger = FakeHarbinger.FakeHarbingerContract(
      harbingerValue = sp.nat(3500000), # $3.50
      harbingerUpdateTime = currentTime,
      harbingerAsset = Constants.ASSET_CODE
    )
    scenario += harbinger

    # AND a fake quipuswap contract
    quipuswap = FakeQuipuswap.FakeQuipuswapContract()
    scenario += quipuswap
    
    # AND a Quipuswap Proxy contract with 20% slippage tolerance
    proxy = QuipuswapProxyContract(
      harbingerContractAddress = harbinger.address,
      quipuswapContractAddress = quipuswap.address,
      slippageTolerance = sp.nat(20)
    )
    scenario += proxy

    # WHEN a trade is initiated
    param = (sp.nat(1), Addresses.LIQUIDITY_POOL_ADDRESS)
    amount = sp.tez(10)
    scenario += proxy.tezToTokenPayment(param).run(
      sender = Addresses.LIQUIDITY_POOL_ADDRESS,
      amount = amount,
      now = currentTime,
    )

    # THEN a trade was attempted with up to 20% slippage
    # Expected Amount = (harbinger price * tez sent) * (1 - slippage tolerance)
    #                 = (3.50 * 10) * (1 - .2)
    #                 = 35.00 * 0.8
    #                 = 28
    scenario.verify(quipuswap.data.amountOut == 28 * Constants.PRECISION)
    scenario.verify(quipuswap.data.destination == Addresses.LIQUIDITY_POOL_ADDRESS)

  @sp.add_test(name="tezToTokenPayment - correctly calculates amount out with no slippage")
  def test():
    scenario = sp.test_scenario()
    
    # GIVEN a moment in time.
    currentTime = sp.timestamp(1000)
    
    # AND fake harbinger contract
    harbinger = FakeHarbinger.FakeHarbingerContract(
      harbingerValue = sp.nat(3500000), # $3.50
      harbingerUpdateTime = currentTime,
      harbingerAsset = Constants.ASSET_CODE
    )
    scenario += harbinger

    # AND a fake quipuswap contract
    quipuswap = FakeQuipuswap.FakeQuipuswapContract()
    scenario += quipuswap
    
    # AND a Quipuswap Proxy contract with no slippage
    proxy = QuipuswapProxyContract(
      harbingerContractAddress = harbinger.address,
      quipuswapContractAddress = quipuswap.address,
      slippageTolerance = sp.nat(0)
    )
    scenario += proxy

    # WHEN a trade is initiated
    param = (sp.nat(1), Addresses.LIQUIDITY_POOL_ADDRESS)
    amount = sp.tez(10)
    scenario += proxy.tezToTokenPayment(param).run(
      sender = Addresses.LIQUIDITY_POOL_ADDRESS,
      amount = amount,
      now = currentTime,
    )

    # THEN a trade was attempted with no slippage.
    # Expected Amount = harbinger price * tez sent
    #                 = 3.50 * 10
    #                 = 35.00
    scenario.verify(quipuswap.data.amountOut == 35 * Constants.PRECISION)
    scenario.verify(quipuswap.data.destination == Addresses.LIQUIDITY_POOL_ADDRESS)

  @sp.add_test(name="tezToTokenPayment - fails if oracle is outdated")
  def test():
    scenario = sp.test_scenario()
    
    # GIVEN a moment in time.
    currentTime = sp.timestamp(1000)
    maxDataDelaySec = sp.nat(30)
    
    # AND fake harbinger contract that is out of date
    lastUpdateTime = sp.timestamp(500)
    harbinger = FakeHarbinger.FakeHarbingerContract(
      harbingerValue = sp.nat(3500000), # $3.50
      harbingerUpdateTime = lastUpdateTime,
      harbingerAsset = Constants.ASSET_CODE
    )
    scenario += harbinger
    
    # AND a Quipuswap Proxy contract
    proxy = QuipuswapProxyContract(
      harbingerContractAddress = harbinger.address,
      maxDataDelaySec = maxDataDelaySec
    )
    scenario += proxy

    # WHEN a trade is initiated
    # THEN the call fails
    param = (sp.nat(123), Addresses.LIQUIDITY_POOL_ADDRESS)
    scenario += proxy.tezToTokenPayment(param).run(
      sender = Addresses.LIQUIDITY_POOL_ADDRESS,
      now = currentTime,

      valid = False,
      exception = Errors.STALE_DATA
    )

  @sp.add_test(name="tezToTokenPayment - fails if contract is paused")
  def test():
    # GIVEN a Quipuswap Proxy contract that is paused
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      paused = True
    )
    scenario += proxy

    # WHEN a trade is initiated
    # THEN the call fails
    param = (sp.nat(123), Addresses.LIQUIDITY_POOL_ADDRESS)
    scenario += proxy.tezToTokenPayment(param).run(
      sender = Addresses.LIQUIDITY_POOL_ADDRESS,

      valid = False,
      exception = Errors.PAUSED
    )

  @sp.add_test(name="tezToTokenPayment - fails if not called by liquidity pool")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS
    )
    scenario += proxy

    # WHEN a trade is initiated by someone other than the liquidity pool
    # THEN the call fails
    param = (sp.nat(123), Addresses.LIQUIDITY_POOL_ADDRESS)
    scenario += proxy.tezToTokenPayment(param).run(
      sender = Addresses.NULL_ADDRESS,

      valid = False,
      exception = Errors.BAD_SENDER
    )

  ################################################################
  # pause
  ################################################################

  @sp.add_test(name="pause - succeeds when called by pause guardian")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      paused = False
    )
    scenario += proxy

    # WHEN pause is called
    scenario += proxy.pause().run(
      sender = Addresses.PAUSE_GUARDIAN_ADDRESS,
    )

    # THEN the contract is paused
    scenario.verify(proxy.data.paused == True)

  @sp.add_test(name="pause - fails when not called by pause guardian")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      paused = False
    )
    scenario += proxy

    # WHEN pause is called is called by someone who isn't the pause guardian THEN the call fails
    scenario += proxy.pause().run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_PAUSE_GUARDIAN
    )

  ################################################################
  # setMaxDataDelaySec
  ################################################################

  @sp.add_test(name="setMaxDataDelaySec - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      maxDataDelaySec = sp.nat(10)
    )
    scenario += proxy

    # WHEN setMaxDataDelaySec is called
    newValue = sp.nat(20)
    scenario += proxy.setMaxDataDelaySec(newValue).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the storage is updated
    scenario.verify(proxy.data.maxDataDelaySec == newValue)

  @sp.add_test(name="setMaxDataDelaySec - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      maxDataDelaySec = sp.nat(10)
    )
    scenario += proxy

    # WHEN setMaxDataDelaySec is called is called by someone who isn't the governor THEN the call fails
    newValue = sp.nat(20)
    scenario += proxy.setMaxDataDelaySec(newValue).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )

  ################################################################
  # setSlippageTolerance
  ################################################################

  @sp.add_test(name="setSlippageTolerance - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      slippageTolerance = sp.nat(10)
    )
    scenario += proxy

    # WHEN setSlippageTolerance is called
    newValue = sp.nat(20)
    scenario += proxy.setSlippageTolerance(newValue).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the storage is updated
    scenario.verify(proxy.data.slippageTolerance == newValue)

  @sp.add_test(name="setSlippageTolerance - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      slippageTolerance = sp.nat(10)
    )
    scenario += proxy

    # WHEN setSlippageTolerance is called is called by someone who isn't the governor THEN the call fails
    newValue = sp.nat(20)
    scenario += proxy.setSlippageTolerance(newValue).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )

  ################################################################
  # unpause
  ################################################################

  @sp.add_test(name="unpause - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      paused = True
    )
    scenario += proxy

    # WHEN unpause is called
    scenario += proxy.unpause().run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is unpaused
    scenario.verify(proxy.data.paused == False)

  @sp.add_test(name="unpause - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    proxy = QuipuswapProxyContract(
      paused = True
    )
    scenario += proxy

    # WHEN unpause is called is called by someone who isn't the governor THEN the call fails
    scenario += proxy.unpause().run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )

  ################################################################
  # setLiquidityPoolContract
  ################################################################

  @sp.add_test(name="setLiquidityPoolContract - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS
    proxy = QuipuswapProxyContract(
      liquidityPoolContractAddress = liquidityPoolContractAddress
    )
    scenario += proxy

    # WHEN the setLiquidityPoolContract is called with a new contract
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setLiquidityPoolContract(rotatedAddress).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    scenario.verify(proxy.data.liquidityPoolContractAddress == rotatedAddress)

  @sp.add_test(name="setLiquidityPoolContract - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    liquidityPoolContractAddress = Addresses.LIQUIDITY_POOL_ADDRESS
    proxy = QuipuswapProxyContract(
      liquidityPoolContractAddress = liquidityPoolContractAddress
    )
    scenario += proxy

    # WHEN the setLiquidityPoolContract is called by someone who isn't the governor THEN the call fails
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setLiquidityPoolContract(rotatedAddress).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )

  ################################################################
  # setHarbingerContract
  ################################################################

  @sp.add_test(name="setHarbingerContract - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    harbingerContractAddress = Addresses.HARBINGER_ADDRESS
    proxy = QuipuswapProxyContract(
      harbingerContractAddress = harbingerContractAddress
    )
    scenario += proxy

    # WHEN the setHarbingerContract is called with a new contract
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setHarbingerContract(rotatedAddress).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    scenario.verify(proxy.data.harbingerContractAddress == rotatedAddress)

  @sp.add_test(name="setHarbingerContract - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    harbingerContractAddress = Addresses.HARBINGER_ADDRESS
    proxy = QuipuswapProxyContract(
      harbingerContractAddress = harbingerContractAddress
    )
    scenario += proxy

    # WHEN the setHarbingerContract is called by someone who isn't the governor THEN the call fails
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setHarbingerContract(rotatedAddress).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )

  ################################################################
  # setPauseGuardianContract
  ################################################################

  @sp.add_test(name="setPauseGuardianContract - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    pauseGuardianContractAddress = Addresses.PAUSE_GUARDIAN_ADDRESS
    proxy = QuipuswapProxyContract(
      pauseGuardianContractAddress = pauseGuardianContractAddress
    )
    scenario += proxy

    # WHEN the setPauseGuardianContract is called with a new contract
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setPauseGuardianContract(rotatedAddress).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    scenario.verify(proxy.data.pauseGuardianContractAddress == rotatedAddress)

  @sp.add_test(name="setPauseGuardianContract - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    pauseGuardianContractAddress = Addresses.PAUSE_GUARDIAN_ADDRESS
    proxy = QuipuswapProxyContract(
      pauseGuardianContractAddress = pauseGuardianContractAddress
    )
    scenario += proxy

    # WHEN the setPauseGuardianContract is called by someone who isn't the governor THEN the call fails
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setPauseGuardianContract(rotatedAddress).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    ) 

  ################################################################
  # setQuipuswapContract
  ################################################################

  @sp.add_test(name="setQuipuswapContract - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    quipuswapContractAddress = Addresses.QUIPUSWAP_ADDRESS
    proxy = QuipuswapProxyContract(
      quipuswapContractAddress = quipuswapContractAddress
    )
    scenario += proxy

    # WHEN the setQuipuswapContract is called with a new contract
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setQuipuswapContract(rotatedAddress).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    scenario.verify(proxy.data.quipuswapContractAddress == rotatedAddress)

  @sp.add_test(name="setQuipuswapContract - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    governorContractAddress = Addresses.GOVERNOR_ADDRESS
    quipuswapContractAddress = Addresses.QUIPUSWAP_ADDRESS
    proxy = QuipuswapProxyContract(
      quipuswapContractAddress = quipuswapContractAddress
    )
    scenario += proxy

    # WHEN the setQuipuswapContract is called by someone who isn't the governor THEN the call fails
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setQuipuswapContract(rotatedAddress).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    ) 

  ################################################################
  # setGovernorContract
  ################################################################

  @sp.add_test(name="setGovernorContract - succeeds when called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    governorContractAddress = Addresses.GOVERNOR_ADDRESS
    proxy = QuipuswapProxyContract(
      governorContractAddress = governorContractAddress
    )
    scenario += proxy

    # WHEN the setGovernorContract is called with a new contract
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setGovernorContract(rotatedAddress).run(
      sender = governorContractAddress,
    )

    # THEN the contract is updated.
    scenario.verify(proxy.data.governorContractAddress == rotatedAddress)

  @sp.add_test(name="setGovernorContract - fails when not called by governor")
  def test():
    # GIVEN a Quipuswap Proxy contract
    scenario = sp.test_scenario()

    governorContractAddress = Addresses.GOVERNOR_ADDRESS
    proxy = QuipuswapProxyContract(
      governorContractAddress = governorContractAddress
    )
    scenario += proxy

    # WHEN the setGovernorContract is called by someone who isn't the governor THEN the call fails
    rotatedAddress = Addresses.ROTATED_ADDRESS
    scenario += proxy.setGovernorContract(rotatedAddress).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False,
      exception = Errors.NOT_GOVERNOR
    )    

  sp.add_compilation_target("quipuswap-proxy", QuipuswapProxyContract())
