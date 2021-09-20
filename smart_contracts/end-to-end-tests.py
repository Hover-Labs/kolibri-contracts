import smartpy as sp

Addresses = sp.import_script_from_url("file:test-helpers/addresses.py")
Constants = sp.import_script_from_url("file:common/constants.py")
DevFund = sp.import_script_from_url("file:dev-fund.py")
Dummy = sp.import_script_from_url("file:test-helpers/dummy-contract.py")
FakeHarbinger = sp.import_script_from_url("file:test-helpers/fake-harbinger.py")
Minter = sp.import_script_from_url("file:minter.py")
Oracle = sp.import_script_from_url("file:oracle.py")
Oven = sp.import_script_from_url("file:oven.py")
OvenFactory = sp.import_script_from_url("file:oven-factory.py")
OvenProxy = sp.import_script_from_url("file:oven-proxy.py")
OvenRegistry = sp.import_script_from_url("file:oven-registry.py")
StabilityFund = sp.import_script_from_url("file:stability-fund.py")
Token= sp.import_script_from_url("file:token.py")

@sp.add_test(name="End to End Tests - Alice can deposit and withdraw from oven")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  stabilityDevFundSplit = sp.nat(100000000000000000) # 10%
  liquidationFeePercent = sp.nat(100000000000000000) # 10%
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    collateralizationPercentage = sp.nat(200000000000000000000), # 200%
    lastInterestIndexUpdateTime = currentTime,
    stabilityDevFundSplit = stabilityDevFundSplit,
    liquidationFeePercent = liquidationFeePercent
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven.
  aliceOven = Oven.OvenContract(owner = alice.address, ovenProxyContractAddress = ovenProxy.address)
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # VERIFY alice can deposit into the oven.
  currentTime = currentTime.add_seconds(1)
  amount = sp.tez(10)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = amount, now = currentTime)
  scenario.verify(aliceOven.balance == amount)

  # VERIFY alice can withdraw from the oven.
  currentTime = currentTime.add_seconds(1)
  scenario += aliceOven.withdraw(amount).run(sender = alice.address, now = currentTime)
  scenario.verify(aliceOven.balance == sp.tez(0))
  scenario.verify(alice.balance == amount)

@sp.add_test(name="End to End Tests - Alice can borrow and repay tokens")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  stabilityDevFundSplit = sp.nat(100000000000000000) # 10%
  liquidationFeePercent = sp.nat(100000000000000000) # 10%
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    collateralizationPercentage = sp.nat(200000000000000000000), # 200%
    lastInterestIndexUpdateTime = currentTime,
    stabilityDevFundSplit = stabilityDevFundSplit,
    liquidationFeePercent = liquidationFeePercent
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven.
  aliceOven = Oven.OvenContract(owner = alice.address, ovenProxyContractAddress = ovenProxy.address)
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # VERIFY alice can deposit into the oven and then mint tokens
  currentTime = currentTime.add_seconds(1)
  amount = sp.tez(10)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = amount, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  borrowAmount = 5 * Constants.PRECISION
  scenario += aliceOven.borrow(borrowAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(aliceOven.balance == amount)
  scenario.verify(token.data.balances[alice.address].balance == borrowAmount)

  # VERIFY alice can repay the borrowed tokens and withdraw collateral.
  currentTime = currentTime.add_seconds(1)
  scenario += aliceOven.repay(borrowAmount).run(sender = alice.address, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  scenario += aliceOven.withdraw(amount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == sp.nat(0))
  scenario.verify(aliceOven.balance == sp.tez(0))
  scenario.verify(alice.balance == amount)

@sp.add_test(name="End to End Tests - Alice can borrow and repay tokens incrementally")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  stabilityDevFundSplit = sp.nat(100000000000000000) # 10%
  liquidationFeePercent = sp.nat(100000000000000000) # 10%
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    collateralizationPercentage = sp.nat(200000000000000000000), # 200%
    lastInterestIndexUpdateTime = currentTime,
    stabilityDevFundSplit = stabilityDevFundSplit,
    liquidationFeePercent = liquidationFeePercent
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven.
  aliceOven = Oven.OvenContract(owner = alice.address, ovenProxyContractAddress = ovenProxy.address)
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # VERIFY alice can withdraw partial amounts of collateral after repaying
  # Alice deposits $20 of XTZ and mints $10 of kUSD
  currentTime = currentTime.add_seconds(1)
  amount = sp.tez(10)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = amount, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  borrowAmount = 10 * Constants.PRECISION
  scenario += aliceOven.borrow(borrowAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 10 * Constants.PRECISION)
  scenario.verify(aliceOven.balance == sp.tez(10))

  # Alice repays $2 of kUSD
  currentTime = currentTime.add_seconds(1)
  repayAmount = 2 * Constants.PRECISION
  scenario += aliceOven.repay(repayAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 8 * Constants.PRECISION)
  scenario.verify(aliceOven.balance == sp.tez(10))

  # Alice can now withdraw $4 of XTZ
  currentTime = currentTime.add_seconds(1)
  withdrawAmount = sp.mutez(2000000)
  scenario += aliceOven.withdraw(withdrawAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 8 * Constants.PRECISION)
  scenario.verify(aliceOven.balance == sp.tez(8))
  scenario.verify(alice.balance == withdrawAmount) 

  # Alice can repay and withdraw all the remaining collateral.
  currentTime = currentTime.add_seconds(1)
  repayAmount = 8 * Constants.PRECISION
  scenario += aliceOven.repay(repayAmount).run(sender = alice.address, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  withdrawAmount = sp.mutez(8000000)
  scenario += aliceOven.withdraw(withdrawAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 0)
  scenario.verify(aliceOven.balance == sp.tez(0))
  scenario.verify(alice.balance == amount) 

@sp.add_test(name="End to End Tests - Bob can liquidate Alices oven")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  stabilityDevFundSplit = sp.nat(100000000000000000) # 10%
  liquidationFeePercent = sp.nat(100000000000000000) # 10%
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    collateralizationPercentage = sp.nat(200000000000000000000), # 200%
    lastInterestIndexUpdateTime = currentTime,
    stabilityDevFundSplit = stabilityDevFundSplit,
    liquidationFeePercent = liquidationFeePercent
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven.
  aliceOven = Oven.OvenContract(owner = alice.address, ovenProxyContractAddress = ovenProxy.address)
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # VERIFY Bob can liquidate an oven. 
  # Alice deposits $20 of XTZ and mints $10 of kUSD
  currentTime = currentTime.add_seconds(1)
  amount = sp.tez(10)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = amount, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  borrowAmount = 10 * Constants.PRECISION
  scenario += aliceOven.borrow(borrowAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 10 * Constants.PRECISION)
  scenario.verify(aliceOven.balance == amount)

  # The price of XTZ crashes to $1, XTZ is now worth $10 and kUSD is worth $10
  scenario += fakeHarbinger.setNewPrice(100000)

  # A new actor, Bob, notices this. Bob has many tokens.
  bob = Dummy.DummyContract()
  scenario += bob

  bobTokenAmount = 100 * Constants.PRECISION
  scenario += token.mint(sp.record(address = bob.address, value = bobTokenAmount)).run(sender = minter.address)
  scenario.verify(token.data.balances[bob.address].balance == bobTokenAmount)

  # Bob liquidates Alice's oven.  
  currentTime = currentTime.add_seconds(1)
  scenario += aliceOven.liquidate(sp.unit).run(sender = bob.address, now = currentTime)

  # Bob loses the tokens needed to repay the collateral.
  liquidationfee = borrowAmount // 10 # 10% of borrowed amount
  bobTokensLessRepayAmount = sp.as_nat(bobTokenAmount - borrowAmount)
  bobTokensLessRepayAmountAndLiquidationFee = sp.as_nat(bobTokensLessRepayAmount - liquidationfee)
  scenario.verify(token.data.balances[bob.address].balance == bobTokensLessRepayAmountAndLiquidationFee)

  # Developer fund received 10% of liquidation fee
  expectedDevFundValue = (borrowAmount // 10) // 10 # 10% of borrowed amount
  scenario.verify(token.data.balances[developerFund.address].balance == expectedDevFundValue)

  # Stability fund received the remainder of the liquidation fee
  expectedStabilityFundValue = ((borrowAmount // 10) // 10) * 9 # 90% of borrowed amount
  scenario.verify(token.data.balances[stabilityFund.address].balance == expectedStabilityFundValue)

  # Bob received the collateral.
  scenario.verify(bob.balance == amount)

  # Alice's oven is now liquidated.
  scenario.verify(aliceOven.data.isLiquidated == True)

@sp.add_test(name="End to End Tests - Stability Fund can liquidate Alices oven")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  stabilityDevFundSplit = sp.nat(100000000000000000) # 10%
  liquidationFeePercent = sp.nat(100000000000000000) # 10%
  administrator = Dummy.DummyContract()
  developerFund = DevFund.DevFundContract(
    administratorContractAddress = administrator.address
  )
  stabilityFund = StabilityFund.StabilityFundContract(
    administratorContractAddress = administrator.address
  )
  minter = Minter.MinterContract(
    collateralizationPercentage = sp.nat(200000000000000000000), # 200%
    lastInterestIndexUpdateTime = currentTime,
    stabilityDevFundSplit = stabilityDevFundSplit,
    liquidationFeePercent = liquidationFeePercent
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += administrator
  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven.
  aliceOven = Oven.OvenContract(owner = alice.address, ovenProxyContractAddress = ovenProxy.address)
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # VERIFY the StabilityFund can liquidate an oven. 
  # Alice deposits $20 of XTZ and mints $10 of kUSD
  currentTime = currentTime.add_seconds(1)
  amount = sp.tez(10)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = amount, now = currentTime)
  currentTime = currentTime.add_seconds(1)
  borrowAmount = 10 * Constants.PRECISION
  scenario += aliceOven.borrow(borrowAmount).run(sender = alice.address, now = currentTime)

  scenario.verify(token.data.balances[alice.address].balance == 10 * Constants.PRECISION)
  scenario.verify(aliceOven.balance == sp.tez(10))

  # The price of XTZ crashes to $1, XTZ is now worth $10 and kUSD is worth $10
  scenario += fakeHarbinger.setNewPrice(100000)

  # The stability fund has many tokens
  stabilityFundTokenAmount = 100 * Constants.PRECISION
  scenario += token.mint(sp.record(address = stabilityFund.address, value = stabilityFundTokenAmount)).run(sender = minter.address)
  scenario.verify(token.data.balances[stabilityFund.address].balance == stabilityFundTokenAmount)

  # The administrator notices Alice's oven is liquidatable and instructs the stability fund to liquidated it.
  currentTime = currentTime.add_seconds(1)
  scenario += stabilityFund.liquidate(aliceOven.address).run(sender = administrator.address, now = currentTime)

  # The stability fund loses the tokens needed to repay the collateral, and gains 90% of the liquidation fee
  liquidationfee = borrowAmount // 10 # 10% of borrowed amount
  stabilityFundTokensLessRepayAmount = sp.as_nat(stabilityFundTokenAmount - borrowAmount)
  stabilityFundTokensLessRepayAmountAndLiquidationFee = sp.as_nat(stabilityFundTokensLessRepayAmount - liquidationfee)
  expectedStabilityFundTokensFromLiquidation = ((borrowAmount // 10) // 10) * 9 # 90% of borrowed amount
  expectedDevFundValue = stabilityFundTokensLessRepayAmountAndLiquidationFee + expectedStabilityFundTokensFromLiquidation
  scenario.verify(token.data.balances[stabilityFund.address].balance == expectedDevFundValue)

  # Developer fund received 10% of liquidation fee
  expectedDevFundValue = (borrowAmount // 10) // 10 # 10% of borrowed amount
  scenario.verify(token.data.balances[developerFund.address].balance == expectedDevFundValue)

  # The stability fund received the collateral.
  scenario.verify(stabilityFund.balance == amount)

  # Alice's oven is now liquidated.
  scenario.verify(aliceOven.data.isLiquidated == True)

  # And the Administrator received no XTZ and has no record of a balance of kUSD
  scenario.verify(administrator.balance == sp.tez(0))
  scenario.verify(token.data.balances.contains(administrator.address) == False)

@sp.add_test(name="End to End Tests - Fees are accrued - Alices oven in sync with minter interest index")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts, which exist at compound period  1
  lastInterestIndexUpdateTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
  stabilityFee = sp.nat(100000000000000000) # 10%
  initialInterestIndex = 1100000000000000000 # 1.10
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    stabilityFee = stabilityFee,
    lastInterestIndexUpdateTime = lastInterestIndexUpdateTime, 
    interestIndex = initialInterestIndex
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven with an interest index the same as the minter.
  aliceBorrowedTokens = 10 * Constants.PRECISION
  aliceStabilityFeeTokens = sp.int(0)
  aliceOven = Oven.OvenContract(
    owner = alice.address, 
    borrowedTokens = aliceBorrowedTokens,
    stabilityFeeTokens = aliceStabilityFeeTokens,
    ovenProxyContractAddress = ovenProxy.address,
    interestIndex = sp.to_int(initialInterestIndex)
  )
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # WHEN alice deposits 1 XTZ at compound period = 2
  currentTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
  depositAmount = sp.tez(1)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = depositAmount, now = currentTime)

  # THEN the minter compounds its interest index for one period
  expectedInterestIndex = 1210000000000000000
  scenario.verify(minter.data.interestIndex == expectedInterestIndex)

  # AND the minter sets the last updated time to the current time.
  scenario.verify(minter.data.lastInterestIndexUpdateTime == currentTime)

  # AND the oven receives the same interest index
  scenario.verify(aliceOven.data.interestIndex == expectedInterestIndex)

  # AND stability tokens compounded once
  newTokensAccruedAsStabilityFeesFromStabilityFees = sp.as_nat(aliceStabilityFeeTokens) // 10
  newTokensAccruedAsStabiiltyFeesFromBorrowedTokens = aliceBorrowedTokens // 10
  expectedStabilityTokensAfterFirstCompound = sp.as_nat(aliceStabilityFeeTokens) + newTokensAccruedAsStabilityFeesFromStabilityFees + newTokensAccruedAsStabiiltyFeesFromBorrowedTokens
  # scenario.verify(expectedStabilityTokensAfterFirstCompound == sp.nat(1000000000000000000)) # Sanity check
  scenario.verify(aliceOven.data.stabilityFeeTokens == sp.to_int(expectedStabilityTokensAfterFirstCompound))

  # WHEN alice deposits 1 XTZ at compound period = 3
  currentTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 3)
  depositAmount = sp.tez(1)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = depositAmount, now = currentTime)

  # THEN the minter compounds its interest index for one period
  expectedInterestIndex = 1331000000000000000
  scenario.verify(minter.data.interestIndex == expectedInterestIndex)

  # AND the minter sets the last updated time to the current time.
  scenario.verify(minter.data.lastInterestIndexUpdateTime == currentTime)

  # AND the oven receives the same interest index
  scenario.verify(aliceOven.data.interestIndex == expectedInterestIndex)

  # AND stability tokens compounded the second time.
  scenario.verify(aliceOven.data.stabilityFeeTokens == sp.to_int(2100000000000000000))

@sp.add_test(name="End to End Tests - Fees are accrued - Alices oven out of sync with minter interest index")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts, which exist at compound period  1
  lastInterestIndexUpdateTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
  stabilityFee = sp.nat(100000000000000000) # 10%
  initialInterestIndex = 1100000000000000000 # 1.10
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    stabilityFee = stabilityFee,
    lastInterestIndexUpdateTime = lastInterestIndexUpdateTime, 
    interestIndex = initialInterestIndex
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven with interest index = 1
  aliceBorrowedTokens = 10 * Constants.PRECISION
  aliceStabilityFeeTokens = sp.int(0)
  aliceOven = Oven.OvenContract(
    owner = alice.address, 
    borrowedTokens = aliceBorrowedTokens,
    stabilityFeeTokens = aliceStabilityFeeTokens,
    ovenProxyContractAddress = ovenProxy.address,
    interestIndex = sp.to_int(Constants.PRECISION)
  )
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # WHEN alice deposits 1 XTZ at compound period = 2
  currentTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
  depositAmount = sp.tez(1)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = depositAmount, now = currentTime)

  # THEN the minter compounds its interest index for one period
  expectedInterestIndex = 1210000000000000000
  scenario.verify(minter.data.interestIndex == expectedInterestIndex)

  # AND the minter sets the last updated time to the current time.
  scenario.verify(minter.data.lastInterestIndexUpdateTime == currentTime)

  # AND the oven receives the same interest index
  scenario.verify(aliceOven.data.interestIndex == expectedInterestIndex)

  # AND stability tokens are compounded twice
  newTokensAccruedAsStabilityFeesFromStabilityFees = sp.as_nat(aliceStabilityFeeTokens) // 10
  newTokensAccruedAsStabiiltyFeesFromBorrowedTokens = aliceBorrowedTokens // 10
  expectedStabilityTokensAfterFirstCompound = sp.as_nat(aliceStabilityFeeTokens) + newTokensAccruedAsStabilityFeesFromStabilityFees + newTokensAccruedAsStabiiltyFeesFromBorrowedTokens
  # scenario.verify(expectedStabilityTokensAfterFirstCompound == sp.nat(1000000000000000000)) # Sanity check
  newTokensAccruedAsStabilityFeesFromStabilityFees = expectedStabilityTokensAfterFirstCompound // 10
  expectedStabilityTokensAfterSecondCompound = expectedStabilityTokensAfterFirstCompound + newTokensAccruedAsStabilityFeesFromStabilityFees + newTokensAccruedAsStabiiltyFeesFromBorrowedTokens
  # scenario.verify(expectedStabilityTokensAfterSecondCompound == sp.nat(2100000000000000000)) # Sanity check
  scenario.verify(aliceOven.data.stabilityFeeTokens == sp.to_int(expectedStabilityTokensAfterSecondCompound))

@sp.add_test(name="End to End Tests - Fees are accrued - multiple time periods elapsed")
def test():
  scenario = sp.test_scenario()

  # GIVEN the beginning of time itself
  currentTime = sp.timestamp(0)

  # AND a fake harbinger contract.
  fakeHarbinger = FakeHarbinger.FakeHarbingerContract(
    harbingerValue = sp.nat(2 * 1000000), # $2
    harbingerUpdateTime = currentTime
  )
  scenario += fakeHarbinger

  # AND a universe of Stablecoin contracts
  lastInterestIndexUpdateTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
  stabilityFee = sp.nat(100000000000000000) # 10%
  initialInterestIndex = 1100000000000000000 # 1.10
  developerFund = DevFund.DevFundContract()
  stabilityFund = StabilityFund.StabilityFundContract()
  minter = Minter.MinterContract(
    stabilityFee = stabilityFee,
    lastInterestIndexUpdateTime = lastInterestIndexUpdateTime, 
    interestIndex = initialInterestIndex
  )
  oracle = Oracle.OracleContract(harbingerContractAddress = fakeHarbinger.address)
  ovenFactory = OvenFactory.OvenFactoryContract()
  ovenProxy = OvenProxy.OvenProxyContract()
  ovenRegistry = OvenRegistry.OvenRegistryContract()
  token = Token.FA12()

  scenario += developerFund
  scenario += stabilityFund
  scenario += minter
  scenario += oracle
  scenario += ovenFactory
  scenario += ovenProxy
  scenario += ovenRegistry
  scenario += token

  # AND a user, Alice.
  alice = Dummy.DummyContract()
  scenario += alice

  # AND the contracts are wired together
  scenario += stabilityFund.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += minter.updateContracts((Addresses.GOVERNOR_ADDRESS, (token.address, (ovenProxy.address, (stabilityFund.address, developerFund.address))))).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setOvenProxyContract(ovenProxy.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenFactory.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setMinterContract(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOvenRegistryContract(ovenRegistry.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += ovenProxy.setOracleContract(oracle.address).run(sender= Addresses.GOVERNOR_ADDRESS)
  scenario += ovenRegistry.setOvenFactoryContract(ovenFactory.address).run(sender = Addresses.GOVERNOR_ADDRESS)
  scenario += token.setAdministrator(minter.address).run(sender = Addresses.GOVERNOR_ADDRESS)

  # AND alice has an oven with interest index = 1
  aliceBorrowedTokens = 10 * Constants.PRECISION
  aliceStabilityFeeTokens = sp.int(0)
  aliceOven = Oven.OvenContract(
    owner = alice.address, 
    borrowedTokens = aliceBorrowedTokens,
    stabilityFeeTokens = aliceStabilityFeeTokens,
    ovenProxyContractAddress = ovenProxy.address,
    interestIndex = sp.to_int(initialInterestIndex)
  )
  scenario += ovenRegistry.addOven((aliceOven.address, alice.address)).run(sender = ovenFactory.address)
  scenario += aliceOven

  # WHEN alice deposits 1 XTZ at compound period = 3
  currentTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 3)
  depositAmount = sp.tez(1)
  scenario += aliceOven.default(sp.unit).run(sender = alice.address, amount = depositAmount, now = currentTime)

  # THEN the minter compounds its interest index for two periods using linear approximatoin
  expectedInterestIndex = 1320000000000000000
  scenario.verify(minter.data.interestIndex == expectedInterestIndex)

  # AND the minter sets the last updated time to the current time.
  scenario.verify(minter.data.lastInterestIndexUpdateTime == currentTime)

  # AND the oven receives the same interest index
  scenario.verify(aliceOven.data.interestIndex == expectedInterestIndex)

  # AND stability tokens are compounded twice using linear approximation
  scenario.verify(aliceOven.data.stabilityFeeTokens == sp.to_int(2000000000000000000))
