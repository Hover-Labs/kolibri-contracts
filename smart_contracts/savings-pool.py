import smartpy as sp

Constants = sp.io.import_script_from_url("file:common/constants.py")
Token = sp.io.import_script_from_url("file:token.py")

################################################################
################################################################
# STATE MACHINE STATES
################################################################
################################################################

IDLE = 0
WAITING_UPDATE_BALANCE = 1
WAITING_REDEEM = 2
WAITING_DEPOSIT = 3

################################################################
################################################################
# CONTRACT
################################################################
################################################################

Addresses = sp.io.import_script_from_url("file:./test-helpers/addresses.py")
Errors = sp.io.import_script_from_url("file:./common/errors.py")
FA12 = sp.io.import_script_from_url("file:./fa12.py")

class SavingsPoolContract(FA12.FA12):
  def __init__(
    self,
    
    # The address of the token contract which will be deposited.
    tokenContractAddress = Addresses.TOKEN_ADDRESS,

    # The governor of the pool.
    governorContractAddress = Addresses.GOVERNOR_ADDRESS,

    # The address of the stability fund.
    stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,

    # The address of the pause guardian
    pauseGuardianContractAddress = Addresses.PAUSE_GUARDIAN_ADDRESS,

    # The interest rate.
    interestRate = sp.nat(123),

    # The last time the interest rate was updated.
    lastInterestCompoundTime = sp.timestamp(0),

    # The initial token balance.
    underlyingBalance = sp.nat(0),

    # Whether the savings rate is paused
    paused = False,

    # The initial state of the state machine.
    state = IDLE,

    # State machine states - exposed for testing.
    savedState_tokensToRedeem = sp.none,
    savedState_redeemer = sp.none,
    savedState_tokensToDeposit = sp.none,
    savedState_depositor = sp.none,

    # Parent class fields
    balances = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)),
    totalSupply = sp.nat(0),
  ):
    token_id = sp.nat(0)

    token_entry = sp.map(
      l = {
        "name": sp.bytes('0x496e7465726573742042656172696e67206b555344'), # Interest Bearing kUSD
        "decimals": sp.bytes('0x3138'), # 18
        "symbol": sp.bytes('0x69626b555344'), # ibkUSD
        "icon": sp.bytes('0x2068747470733a2f2f6b6f6c696272692d646174612e73332e616d617a6f6e6177732e636f6d2f6c6f676f2e706e67') # https://kolibri-data.s3.amazonaws.com/logo.png
      },
      tkey = sp.TString,
      tvalue = sp.TBytes
    )
    token_metadata = sp.big_map(
      l = {
        token_id: sp.record(token_id = 0, token_info = token_entry)
      },
      tkey = sp.TNat,
      tvalue = sp.TRecord(token_id = sp.TNat, token_info = sp.TMap(sp.TString, sp.TBytes))
    )

    metadata_data = sp.utils.bytes_of_string('{ "name": "Interest Bearing kUSD",  "description": "Interest Bearing kUSD",  "authors": ["Hover Labs <hello@hover.engineering>"],  "homepage":  "https://kolibri.finance", "interfaces": [ "TZIP-007-2021-01-29"] }')
    metadata = sp.big_map(
      l = {
        "": sp.bytes('0x74657a6f732d73746f726167653a64617461'), # "tezos-storage:data"
        "data": metadata_data
      },
      tkey = sp.TString,
      tvalue = sp.TBytes            
    )

    self.exception_optimization_level = "DefaultUnit"

    self.init(
      # Parent class fields
      balances = balances, 
      totalSupply = totalSupply,

      # Metadata
      metadata = metadata,
      token_metadata = token_metadata,

      # Addresses
      governorContractAddress = governorContractAddress,
      stabilityFundContractAddress = stabilityFundContractAddress,
      tokenContractAddress = tokenContractAddress,
      pauseGuardianContractAddress = pauseGuardianContractAddress,

      # Configuration
      interestRate = interestRate,

      # Internal State
      underlyingBalance = underlyingBalance,
      lastInterestCompoundTime = lastInterestCompoundTime,
      paused = paused,

      # State machine
      state = state,
      savedState_tokensToRedeem = savedState_tokensToRedeem, # Amount of tokens to redeem, populated when state = WAITING_REDEEM
      savedState_redeemer = savedState_redeemer, # Account redeeming tokens, populated when state = WAITING_REDEEM
      savedState_tokensToDeposit = savedState_tokensToDeposit, # Amount of tokens to deposit, populated when state = WAITING_DEPOSIT
      savedState_depositor = savedState_depositor, # Account depositing the tokens, populated when state = WAITING_DEPOSIT
    )

  ################################################################
  # Liquidity Provider Tokens
  ################################################################

  # Deposit a number of tokens and receive LP tokens.
  @sp.entry_point
  def deposit(self, tokensToDeposit):
    sp.set_type(tokensToDeposit, sp.TNat)

    # Validate state
    sp.verify(self.data.state == IDLE, Errors.BAD_STATE)

    # Validate not paused
    sp.verify(self.data.paused == False, Errors.PAUSED)

    # Save state
    self.data.state = WAITING_DEPOSIT
    self.data.savedState_tokensToDeposit = sp.some(tokensToDeposit)
    self.data.savedState_depositor = sp.some(sp.sender)

    # Call token contract to update balance.
    param = (sp.self_address, sp.self_entry_point(entry_point = 'deposit_callback'))
    contractHandle = sp.contract(
      sp.TPair(sp.TAddress, sp.TContract(sp.TNat)),
      self.data.tokenContractAddress,
      "getBalance",      
    ).open_some()
    sp.transfer(param, sp.mutez(0), contractHandle)

  # Private callback for deposit.
  @sp.entry_point
  def deposit_callback(self, updatedBalance):
    sp.set_type(updatedBalance, sp.TNat)

    # Validate sender
    sp.verify(sp.sender == self.data.tokenContractAddress, Errors.BAD_SENDER)

    # Validate state
    sp.verify(self.data.state == WAITING_DEPOSIT, Errors.BAD_STATE)

    # Calculate the newly accrued interest.
    accruedInterest = self.accrueInterest()

    # Calculate the tokens to issue.
    tokensToDeposit = sp.local('tokensToDeposit', self.data.savedState_tokensToDeposit.open_some())
    newTokens = sp.local('newTokens', tokensToDeposit.value * Constants.PRECISION)
    sp.if self.data.totalSupply != sp.nat(0):
      newUnderlyingBalance = sp.local('newUnderlyingBalance', updatedBalance + accruedInterest + tokensToDeposit.value)
      fractionOfPoolOwnership = sp.local('fractionOfPoolOwnership', (tokensToDeposit.value * Constants.PRECISION) / newUnderlyingBalance.value)
      newTokens.value = ((fractionOfPoolOwnership.value * self.data.totalSupply) / (sp.as_nat(Constants.PRECISION - fractionOfPoolOwnership.value)))

    # Debit underlying balance by the amount of tokens that will be sent
    self.data.underlyingBalance = updatedBalance + accruedInterest + tokensToDeposit.value

    # Transfer tokens to this contract.
    depositor = sp.local('depositor', self.data.savedState_depositor.open_some())
    tokenTransferParam = sp.record(
      from_ = depositor.value,
      to_ = sp.self_address, 
      value = tokensToDeposit.value
    )
    transferHandle = sp.contract(
      sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
      self.data.tokenContractAddress,
      "transfer"
    ).open_some()
    sp.transfer(tokenTransferParam, sp.mutez(0), transferHandle)

    # Mint tokens to the depositor
    tokenMintParam = sp.record(
      address = depositor.value, 
      value = newTokens.value
    )
    mintHandle = sp.contract(
      sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")),
      sp.self_address,
      entry_point = 'mint',
    ).open_some()
    sp.transfer(tokenMintParam, sp.mutez(0), mintHandle)

    # Reset state
    self.data.state = IDLE
    self.data.savedState_tokensToDeposit = sp.none
    self.data.savedState_depositor = sp.none

  # Redeem a number of LP tokens for the underlying asset.
  @sp.entry_point
  def redeem(self, tokensToRedeem):
    sp.set_type(tokensToRedeem, sp.TNat)

    # Validate state
    sp.verify(self.data.state == IDLE, Errors.BAD_STATE)

    # Validate not paused
    sp.verify(self.data.paused == False, Errors.PAUSED)

    # Save state
    self.data.state = WAITING_REDEEM
    self.data.savedState_tokensToRedeem = sp.some(tokensToRedeem)
    self.data.savedState_redeemer = sp.some(sp.sender)

    # Call token contract to update balance.
    param = (sp.self_address, sp.self_entry_point(entry_point = 'redeem_callback'))
    contractHandle = sp.contract(
      sp.TPair(sp.TAddress, sp.TContract(sp.TNat)),
      self.data.tokenContractAddress,
      "getBalance",      
    ).open_some()
    sp.transfer(param, sp.mutez(0), contractHandle)

  # Private callback for redeem.
  @sp.entry_point
  def redeem_callback(self, updatedBalance):
    sp.set_type(updatedBalance, sp.TNat)

    # Validate sender
    sp.verify(sp.sender == self.data.tokenContractAddress, Errors.BAD_SENDER)

    # Validate state
    sp.verify(self.data.state == WAITING_REDEEM, Errors.BAD_STATE)

    # Calculate the newly accrued interest.
    accruedInterest = self.accrueInterest()

    # Calculate tokens to receive.
    tokensToRedeem = sp.local('tokensToRedeem', self.data.savedState_tokensToRedeem.open_some())
    fractionOfPoolOwnership = sp.local('fractionOfPoolOwnership', (tokensToRedeem.value * Constants.PRECISION) // self.data.totalSupply)
    tokensToReceive = sp.local('tokensToReceive', (fractionOfPoolOwnership.value * (updatedBalance + accruedInterest)) / Constants.PRECISION)

    # Debit underlying balance by the amount of tokens that will be sent
    # TODO(keefertaylor): Test.
    self.data.underlyingBalance = sp.as_nat(updatedBalance + accruedInterest - tokensToReceive.value)

    # Burn the tokens being redeemed.
    redeemer = sp.local('redeemer', self.data.savedState_redeemer.open_some())
    tokenBurnParam = sp.record(
      address = redeemer.value, 
      value = tokensToRedeem.value
    )
    burnHandle = sp.contract(
      sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")),
      sp.self_address,
      entry_point = 'burn',
    ).open_some()
    sp.transfer(tokenBurnParam, sp.mutez(0), burnHandle)

    # Transfer tokens to the owner.
    tokenTransferParam = sp.record(
      from_ = sp.self_address,
      to_ = redeemer.value, 
      value = tokensToReceive.value
    )
    transferHandle = sp.contract(
      sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
      self.data.tokenContractAddress,
      "transfer"
    ).open_some()
    sp.transfer(tokenTransferParam, sp.mutez(0), transferHandle)

    # Reset state
    self.data.state = IDLE
    self.data.savedState_tokensToRedeem = sp.none
    self.data.savedState_redeemer = sp.none

  # Unsafe way to redeem a number of LP tokens for the underlying asset.
  #
  # Users should prefer to call redeem.
  #
  # This entry point does *not* accrue interest for the underlying balance. Using this entrypoint
  # means that the calling LP will forego some of their rewards. This entry point is useful in the 
  # case that the stability fund will not or cannot pay rewards and LPs want to extract their collateral. This entrypoint
  # is also not subject to the pause guardian, ensuring that users can always retrieve assets without interest.
  @sp.entry_point
  def UNSAFE_redeem(self, tokensToRedeem):
    sp.set_type(tokensToRedeem, sp.TNat)

    # Validate state
    sp.verify(self.data.state == IDLE, Errors.BAD_STATE)

    # Calculate tokens to receive.
    fractionOfPoolOwnership = sp.local('fractionOfPoolOwnership', (tokensToRedeem * Constants.PRECISION) / self.data.totalSupply)
    tokensToReceive = sp.local('tokensToReceive', (fractionOfPoolOwnership.value * self.data.underlyingBalance) / Constants.PRECISION)

    # Debit underlying balance by the amount of tokens that will be sent
    self.data.underlyingBalance = sp.as_nat(self.data.underlyingBalance - tokensToReceive.value)

    # Burn the tokens being redeemed.
    tokenBurnParam = sp.record(
      address = sp.sender, 
      value = tokensToRedeem
    )
    burnHandle = sp.contract(
      sp.TRecord(address = sp.TAddress, value = sp.TNat).layout(("address", "value")),
      sp.self_address,
      entry_point = 'burn',
    ).open_some()
    sp.transfer(tokenBurnParam, sp.mutez(0), burnHandle)

    # Transfer tokens to the owner.
    tokenTransferParam = sp.record(
      from_ = sp.self_address,
      to_ = sp.sender, 
      value = tokensToReceive.value
    )
    transferHandle = sp.contract(
      sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
      self.data.tokenContractAddress,
      "transfer"
    ).open_some()
    sp.transfer(tokenTransferParam, sp.mutez(0), transferHandle)

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

  # Update the governor address.
  @sp.entry_point
  def setGovernorContract(self, newGovernorContractAddress):
    sp.set_type(newGovernorContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)
    self.data.governorContractAddress = newGovernorContractAddress

  # Update the stability fund address.
  @sp.entry_point
  def setStabilityFundContract(self, newStabilityFundContractAddress):
    sp.set_type(newStabilityFundContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)
    self.data.stabilityFundContractAddress = newStabilityFundContractAddress   

  # Update the pause guardian address.
  @sp.entry_point
  def setPauseGuardianContract(self, newPauseGuardianContractAddress):
    sp.set_type(newPauseGuardianContractAddress, sp.TAddress)

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)
    self.data.pauseGuardianContractAddress = newPauseGuardianContractAddress

  # Update the interest rate.
  @sp.entry_point
  def setInterestRate(self, newInterestRate):
    sp.set_type(newInterestRate, sp.TNat)

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)

    # Accrue interest.
    accruedInterest = self.accrueInterest() 
    self.data.underlyingBalance = self.data.underlyingBalance + accruedInterest

    # Adjust rate
    self.data.interestRate = newInterestRate   

  # Update contract metadata
  @sp.entry_point	
  def setContractMetadata(self, params):	
    sp.set_type(params, sp.TPair(sp.TString, sp.TBytes))	

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)

    key = sp.fst(params)
    value = sp.snd(params)	
    self.data.metadata[key] = value

  # Update token metadata
  @sp.entry_point	
  def setTokenMetadata(self, params):	
    sp.set_type(params, sp.TRecord(token_id = sp.TNat, token_info = sp.TMap(sp.TString, sp.TBytes)))	

    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)

    self.data.token_metadata[0] = params

  # Rescue any XTZ that may have been sent to the contract.
  @sp.entry_point	
  def rescueXTZ(self, params):
    sp.set_type(params, sp.TRecord(destinationAddress = sp.TAddress).layout("destinationAddress"))

    # Verify the requester is the governor.
    sp.verify(sp.sender == self.data.governorContractAddress, Errors.NOT_GOVERNOR)

    sp.send(params.destinationAddress, sp.balance)    

  # Unpause the system.
  @sp.entry_point
  def unpause(self):
    sp.verify(sp.sender == self.data.governorContractAddress, message = Errors.NOT_GOVERNOR)
    self.data.paused = False

  ###############################################################
  # Views
  ###############################################################

  # Get the total number of kUSD that will be in the pool next time interest accrues.
  @sp.offchain_view(pure = True)
  def offchainView_poolSize(self):
    getInterestAccrualResults = sp.build_lambda(self.getInterestAccrualResults.f)

    interestAccrualResults = getInterestAccrualResults(
      sp.record(
        interestRate = self.data.interestRate,
        lastInterestCompoundTime = self.data.lastInterestCompoundTime,
        underlyingBalance = self.data.underlyingBalance,
      )
    )
    totalPoolSize = self.data.underlyingBalance + interestAccrualResults.accruedInterest
    
    sp.result(totalPoolSize)

  # Get the conversion rate of one LP token to kUSD. Results are denominated in kUSD, with 18 digits
  # of precision.
  @sp.offchain_view(pure = True)
  def offchainView_getLPTokenConversionRate(self):
    # Tabulate the total pool size.
    # TODO(keefertaylor): This is a re-implementation of the logic in `offchainView_poolSize`, attempt to code share
    getInterestAccrualResults = sp.build_lambda(self.getInterestAccrualResults.f)
    interestAccrualResults = getInterestAccrualResults(
      sp.record(
        interestRate = self.data.interestRate,
        lastInterestCompoundTime = self.data.lastInterestCompoundTime,
        underlyingBalance = self.data.underlyingBalance,
      )
    )
    totalPoolSize = self.data.underlyingBalance + interestAccrualResults.accruedInterest

    # Avoid divide by 0 errors if no LP tokens are issued.
    conversionRate = sp.local('conversionRate', sp.nat(0))
    sp.if self.data.totalSupply != sp.nat(0):
      # NOTE: KSR is denominated in 36 digits, and kUSD uses 18 so we upscale the kUSD size to be 
      #       the same precision.
      conversionRate.value = ((totalPoolSize * Constants.PRECISION * Constants.PRECISION) / self.data.totalSupply)
    
    sp.result(conversionRate.value)
    
  # Get the balance of an account in kUSD, if the account redeemed all their LP tokens. Results are 
  # denominated in kUSD, with 18 digits of precision.
  # Get the conversion rate of one LP token to kUSD. Results are denominated in kUSD, with 18 digits
  # of precision.
  @sp.offchain_view(pure = True)
  def offchainView_getAccountValue(self, address):
    sp.set_type(address, sp.TAddress)

    # Tabulate the total pool size.
    # TODO(keefertaylor): This is a re-implementation of the logic in `offchainView_poolSize`, attempt to code share
    getInterestAccrualResults = sp.build_lambda(self.getInterestAccrualResults.f)
    interestAccrualResults = getInterestAccrualResults(
      sp.record(
        interestRate = self.data.interestRate,
        lastInterestCompoundTime = self.data.lastInterestCompoundTime,
        underlyingBalance = self.data.underlyingBalance,
      )
    )
    totalPoolSize = self.data.underlyingBalance + interestAccrualResults.accruedInterest

    # Avoid divide by 0 errors if no LP tokens are issued.
    # TODO(keefertaylor): This is a re-implementation of the logic in `offchainView_poolSize`, attempt to code share
    conversionRate = sp.local('conversionRate', sp.nat(0))
    sp.if self.data.totalSupply != sp.nat(0):
      # NOTE: KSR is denominated in 36 digits, and kUSD uses 18 so we upscale the kUSD size to be 
      #       the same precision.
      conversionRate.value = ((totalPoolSize * Constants.PRECISION * Constants.PRECISION) / self.data.totalSupply)

    # Get account balance.
    # Default to 0 to avoid a bad map access.
    accountLPTokens = sp.nat(0)
    sp.if self.data.balances.contains(address):
      accountLPTokens = self.data.balances[address].balance

    # Return conversion rate of one LP token multipled the number of LP tokens owned.
    # NOTE: KSR is denominated in 36 digits, and kUSD uses 18 so we upscale the kUSD size to be 
    #       the same precision. Then, two fixed point numbers with 36 digits of precision are
    #       multiplied together, which means we need to divide by the LP_TOKEN_PRECISION.
    accountValue = accountLPTokens * conversionRate.value // Constants.LP_TOKEN_PRECISION
    sp.result(accountValue)

  ################################################################
  # Helpers
  ################################################################

  # Helper function to:
  # - Calculate elapsed periods
  # - Accrue interest using linear approximation
  # - Request funds
  #
  # This functionality is split out for re-use across multiple entrypoints and for testing purposes.
  #
  # Param: unit
  # Return: The newly accrued interest
  @sp.sub_entry_point
  def accrueInterest(self):
    # Inline the `getInterestAccrualResults` `global_lambda` for later use in this 
    # `sub_entry_point`.
    # 
    # This is necessary because `sub_entry_point`s cannot call `global_lambda`, and this 
    # functionality needs to be split into a global_lambda for reuse in offchain_view code. See 
    # "Implementation Notes" in the `getInterestAccrualResults` documentation.
    #  
    # Implementation Note: 
    # `sp.build_lambda` will inline the code in the global lambda into this `sub_entry_point`, which
    # effectively duplicates the code and increases contract size. A more elegant solution and space
    # efficient solution would be to pass these lambdas as parameters of the sub_entry_point, but 
    # this contract is not space constrained and that method is more prone to programmer error.
    # For more details, see conversation between messages: 
    #   https://t.me/SmartPy_io/17252 and https://t.me/SmartPy_io/17428 
    getInterestAccrualResults = sp.build_lambda(self.getInterestAccrualResults.f)
    
    # Calculate the results of interest accrual via a pure `global_lambda`.
    interestAccrualResults = sp.local(
      'interestAccrualResults', 
      getInterestAccrualResults(
        sp.record(
          interestRate = self.data.interestRate,
          lastInterestCompoundTime = self.data.lastInterestCompoundTime,
          underlyingBalance = self.data.underlyingBalance,
        )
      )
    )

    # Update the contracts state with the result of the `global_lambda`
    self.data.lastInterestCompoundTime = self.data.lastInterestCompoundTime.add_seconds(
      sp.to_int(
        interestAccrualResults.value.numberOfElapsedInterestPeriods * Constants.SECONDS_PER_COMPOUND
      )
    )

    # Transfer in the required number of tokens from the stability fund.
    stabilityFundHandle = sp.contract(
      sp.TNat,
      self.data.stabilityFundContractAddress,
      'accrueInterest'
    ).open_some()
    sp.transfer(interestAccrualResults.value.accruedInterest, sp.mutez(0), stabilityFundHandle)

    # Return the number of newly accrued tokens.
    sp.result(interestAccrualResults.value.accruedInterest)

  # Helper lambda to calculate data about interest accrual.
  #
  # ================================================================================================
  # Values Calculated
  # ================================================================================================
  #
  # This lambda calculates two pieces of data:
  #
  # 1. The number of interest periods that elapsed.
  #    
  #    If the `lastInterestCompoundTime` is set to `t` seconds, and the current time is `T` seconds,
  #    and a compound period is `c` seconds long, then the number of elapsed interest periods is:
  #      numberOfElapsedInterestPeriods = floor((T - t) / c)
  #
  #    In other words, this calculates the number of interest periods which have *fully* elapsed, 
  #    discarding any partial periods. The value of `lastInterestCompoundTime` should then be 
  #    incremented by the number of periods elapsed and the seconds per period:
  #      newLastInterestCompoundTime = 
  #         lastInterestCompoundTime + (numberOfElapsedInterestPeriods * c)
  # 
  # 2. The newly accrued interest over the current time.
  #
  #     If the current balance of the pool is `i`, and after `n` interest accrual periods at rate 
  #     `r`, the balance of the pool will be `I`, then the accrued interest is:
  #       accruedInterest = `I - i`
  #     
  #     In other words, this value will calculate the amount of interest that needs to be requested 
  #     from the stability fund.
  #    
  # ================================================================================================
  # Implementation Notes
  # ================================================================================================
  # 
  # This functionality is split into a global lambda so that it can be shared between 
  # `sub_entry_point`s and `offchain_views`. By using a `global_lambda` functionality can be reused 
  # and shared, with some caveats. 
  # 
  # A `global_lambda` is required because:
  # - `deposit` and `withdraw` both need to share logic which modifies contract state, necessitating
  #    the use of a shared `sub_entry_point` (And `global_lambda`s cannot modify state)
  # - The values derived by the code in this lambda are needed in `offchain_view`s to calculate 
  #   return values
  # - `offchain_view`s cannot call `sub_entry_point`s but can call `global_lambdas`
  # - `sub_entry_point`s can inline functionality from global lambdas in order to reuse the code. 
  # For more details, see conversation between messages: 
  #     https://t.me/SmartPy_io/17252 and https://t.me/SmartPy_io/17428 
  #
  # Since this data must be a global lambda, the following rules apply:
  # 1. The lambda is completely pure and cannot modify state, only return results. The caller is 
  #    responsible for modifying contract state.
  # 2. The lambda cannot access or modify smart contract storage. Therefore, the smart contract 
  #    storage to be operated on must bein passed in as arguments, even though they should always be
  #    set to the same valuees. 
  #
  # In practice, the above means:
  # 1. This lambda should only ever be called from:
  #   a) The `accrueInterest` sub_entry_point, which provides strong guarantees around contract 
  #      state being updated correctly
  #   b) A view, which does not modify state and simply returns the state of the world to a caller
  # 2. This lambda should ALWAYS be called with the following parameter, which simply maps in the 
  #    contract storage into the lambda:
  #       ```
  #       getInterestAccrualResults(
  #         sp.record(
  #           interestRate = self.data.interestRate,
  #           lastInterestCompoundTime = self.data.lastInterestCompoundTime,
  #           underlyingBalance = self.data.underlyingBalance,
  #         )
  #       )
  #       ```
  #
  # Params:
  # - interestRate (nat): The current interest rate. `self.data.interestRate` should ALWAYS be 
  #                       passed as this argument.
  # - lastInterestCompoundTime (timestamp): The last interest compound time. 
  #                                        `self.data.lastlastInterestCompoundTime` should ALWAYS be
  #                                         passed as this argument.
  # - underlyingBalance (nat): The value of the pool at current time. `self.data.underlyingBalance` 
  #                            should ALWAYS be passed as this argument.
  #
  # Returns: A record of type
  #          `sp.TRecord(accruedInterest = sp.TNat, numberOfElapsedInterestPeriods = sp.TNat)`
  # - accruedInterest (nat): The amount of interest the pool should accrue on `underlyingBalance` of
  #                          value, between `lastInterestCompoundTime` and the current time, when 
  #                          accrued at `interestRate`.
  #                          See: "Values Calculated", point 2.
  # - numberOfElapsedInterestPeriods (nat): The amount of interest accrual periods which fully 
  #                                         elapsed between `lastInterestCompoundTime` and the 
  #                                         current time.
  #                                         See: "Values Calculated", point 1.
  @sp.global_lambda
  def getInterestAccrualResults(param):
    sp.set_type(
      param,
      sp.TRecord(
        interestRate = sp.TNat,
        lastInterestCompoundTime = sp.TTimestamp,
        underlyingBalance = sp.TNat        
      )
    )
    
    # Calculate the number of elapsed interest periods.
    timeDeltaSeconds = sp.as_nat(sp.now - param.lastInterestCompoundTime)
    numberOfElapsedInterestPeriods = sp.local(
      'numberOfElapsedInterestPeriods', 
      timeDeltaSeconds // Constants.SECONDS_PER_COMPOUND
    )

    # Calculate the accrued interest.
    newUnderlyingBalance = param.underlyingBalance * (Constants.PRECISION + (numberOfElapsedInterestPeriods.value * param.interestRate)) // Constants.PRECISION
    accruedInterest = sp.local(
      'accruedInterest', 
      sp.as_nat(newUnderlyingBalance - param.underlyingBalance)
    )

    # Return a tuple containing the number of elapsed periods and the accrued interest
    sp.result(
      sp.record(
        accruedInterest = accruedInterest.value,
        numberOfElapsedInterestPeriods = numberOfElapsedInterestPeriods.value,
      )
    )

################################################################
################################################################
# TESTS
################################################################
################################################################

# Only run tests if this file is main.
if __name__ == "__main__":

  Dummy = sp.io.import_script_from_url("file:./test-helpers/dummy-contract.py")
  Oven = sp.io.import_script_from_url("file:./oven.py")
  StabilityFund = sp.io.import_script_from_url("file:./stability-fund.py")
  Token = sp.io.import_script_from_url("file:./token.py")

  ################################################################
  # Test Helpers
  ################################################################

  # Tests the Accrue Interest sub_entry_point
  # See: https://t.me/SmartPy_io/9155
  class AccrueInterestTester(sp.Contract):
    def __init__(
      self,
      poolContract,
      interestRate,
      lastInterestCompoundTime,
      stabilityFundContractAddress,
      underlyingBalance
    ):
      # Entrypoint under test.
      self.contractEntrypoint = poolContract.accrueInterest

      # The accrue interest entrypoint needs to inline the following lambdas, so the 
      # Tester should also grab reference to them. 
      # For details, see comments in the `accrueInterest` sub_entry_point.
      self.getInterestAccrualResults = poolContract.getInterestAccrualResults

      self.init(
        result = sp.none, 
        interestRate = interestRate,
        lastInterestCompoundTime = lastInterestCompoundTime,
        stabilityFundContractAddress = stabilityFundContractAddress,
        underlyingBalance = underlyingBalance,
      )
        
    @sp.entry_point
    def testContractEntryPoint(self):
      self.data.result = sp.some(self.contractEntrypoint())

  ################################################################
  # accrueInterest
  ################################################################

  @sp.add_test(name="accrueInterest - updates lastInterestCompoundTime for one period")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(0)
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = sp.nat(0)
    )
    scenario += tester

    # WHEN interest is accrued after 1 compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the last interest update time is updated.
    scenario.verify(tester.data.lastInterestCompoundTime == sp.timestamp(Constants.SECONDS_PER_COMPOUND))

  @sp.add_test(name="accrueInterest - updates lastInterestCompoundTime for two periods")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(0)
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = sp.nat(0)
    )
    scenario += tester

    # WHEN interest is accrued after 2 compound periods.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
    )

    # THEN the last interest update time is updated.
    scenario.verify(tester.data.lastInterestCompoundTime == sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2))

  @sp.add_test(name="accrueInterest - updates lastInterestCompoundTime for one period with nonzero start")
  def test():
    # GIVEN a Pool contract with a previous interest update time.
    scenario = sp.test_scenario()

    interestRate = sp.nat(0)
    lastInterestCompoundTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = sp.nat(0)
    )
    scenario += tester

    # WHEN interest is accrued after 1 compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
    )

    # THEN the last interest update time is updated.
    scenario.verify(tester.data.lastInterestCompoundTime == sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2))

  @sp.add_test(name="accrueInterest - updates lastInterestCompoundTime by flooring partial periods")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(0)
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = sp.nat(0)
    )
    scenario += tester
    
    # WHEN interest is accrued after 2.5 periods
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(150) # 2.5 periods
    )

    # THEN the last interest update time is floored.
    scenario.verify(tester.data.lastInterestCompoundTime == sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2))    

  @sp.add_test(name="accrueInterest - calculates accrued interest for one period")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = initialValue
    )
    scenario += tester

    # WHEN interest is accrued after 1 compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the the accrued interest is calculated correctly.
    scenario.verify(tester.data.result.open_some() == sp.as_nat(1100000000000000000 - initialValue))

  @sp.add_test(name="accrueInterest - calculates accrued interest for two periods")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = initialValue
    )
    scenario += tester

    # WHEN interest is accrued after 2 compound periods.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
    )

    # THEN the the accrued interest is calculated correctly.
    scenario.verify(tester.data.result.open_some() == sp.as_nat(1200000000000000000 - initialValue))

  @sp.add_test(name="accrueInterest - calculates accrued interest for one period with nonzero start")
  def test():
    # GIVEN a Pool contract with a previous interest update time.
    scenario = sp.test_scenario()

    interestRate = sp.nat(100000000000000000)
    initialValue = 1100000000000000000
    lastInterestCompoundTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = initialValue
    )
    scenario += tester

    # WHEN interest is accrued after 1 compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND * 2)
    )

    # THEN the the accrued interest is calculated correctly.
    scenario.verify(tester.data.result.open_some() == sp.as_nat(1210000000000000000 - initialValue))

  @sp.add_test(name="accrueInterest - calculates accrued interest by flooring partial periods")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = Addresses.STABILITY_FUND_ADDRESS,
      underlyingBalance = initialValue
    )
    scenario += tester

    # WHEN interest is accrued after 2.5 periods
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(150) # 2.5 periods
    )

    # THEN the the accrued interest is calculated correctly.
    scenario.verify(tester.data.result.open_some() == sp.as_nat(1200000000000000000 - initialValue))

  @sp.add_test(name="accrueInterest - retrieves stability fees for one period")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract.
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a Pool contract
    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a stability fund contract.
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = stabilityFund.address,
      underlyingBalance = initialValue
    )
    scenario += tester

    # AND the tester has the initial underlying balance.
    scenario += token.mint(
      sp.record(
        address = tester.address,
        value = initialValue
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the stability fund is wired to the tester.
    scenario += stabilityFund.setSavingsAccountContract(
      tester.address
    ).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # WHEN interest is accrued after 1 compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the contract has the right number of tokens.
    scenario.verify(token.data.balances[tester.address].balance == 1100000000000000000)

  @sp.add_test(name="accrueInterest - retrieves stability fees for two periods")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract.
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a Pool contract
    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a stability fund contract.
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = stabilityFund.address,
      underlyingBalance = initialValue
    )
    scenario += tester

    # AND the tester has the initial underlying balance.
    scenario += token.mint(
      sp.record(
        address = tester.address,
        value = initialValue
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the stability fund is wired to the tester.
    scenario += stabilityFund.setSavingsAccountContract(
      tester.address
    ).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # WHEN interest is accrued after 2 compound periods.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(2 * Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the contract has the right number of tokens.
    scenario.verify(token.data.balances[tester.address].balance == 1200000000000000000)    

  @sp.add_test(name="accrueInterest - retrieves stability fees for one periods starting at nonzero")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract.
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a Pool contract 
    interestRate = sp.nat(100000000000000000)    
    initialValue = sp.nat(1100000000000000000)
    lastInterestCompoundTime = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a stability fund contract.
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = stabilityFund.address,
      underlyingBalance = initialValue
    )
    scenario += tester

    # AND the tester has the initial underlying balance.
    scenario += token.mint(
      sp.record(
        address = tester.address,
        value = initialValue
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the stability fund is wired to the tester.
    scenario += stabilityFund.setSavingsAccountContract(
      tester.address
    ).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # WHEN interest is accrued after the second compound period.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(2 * Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the contract has the right number of tokens.
    scenario.verify(token.data.balances[tester.address].balance == 1210000000000000000)        

  @sp.add_test(name="accrueInterest - correctly floors partial periods")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract.
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a Pool contract
    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)    
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime
    )
    scenario += pool

    # AND a stability fund contract.
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a tester.
    tester = AccrueInterestTester(
      pool,
      interestRate = interestRate,
      lastInterestCompoundTime = lastInterestCompoundTime,
      stabilityFundContractAddress = stabilityFund.address,
      underlyingBalance = initialValue
    )
    scenario += tester

    # AND the tester has the initial underlying balance.
    scenario += token.mint(
      sp.record(
        address = tester.address,
        value = initialValue
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the stability fund is wired to the tester.
    scenario += stabilityFund.setSavingsAccountContract(
      tester.address
    ).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # WHEN interest is accrued after 2 and a half compound periods.
    scenario += tester.testContractEntryPoint().run(
      now = sp.timestamp(150) # 2.5 periods
    )

    # THEN the contract has the right number of tokens.
    scenario.verify(token.data.balances[tester.address].balance == 1200000000000000000)    

  ################################################################
  # rescueXTZ
  ################################################################

  @sp.add_test(name="rescueXTZ - fails if not called by governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()

    # AND the contract has some XTZ
    xtzAmount = sp.tez(10)
    pool.set_initial_balance(xtzAmount)
    scenario += pool

    # WHEN rescue XTZ is called by someone other than the governor.
    # THEN the call fails.
    notGovernor = Addresses.NULL_ADDRESS
    scenario += pool.rescueXTZ(
      sp.record(
        destinationAddress = Addresses.ALICE_ADDRESS
      )
    ).run(
      sender = notGovernor,
      valid = False
    )

  @sp.add_test(name="rescueXTZ - rescues XTZ")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract(
      governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    )
    xtzAmount = sp.mutez(10)
    pool.set_initial_balance(xtzAmount)
    scenario += pool

    scenario.verify(pool.balance == xtzAmount)

    # AND a dummy contract that will receive the XTZ
    dummy = Dummy.DummyContract()
    scenario += dummy

    # WHEN rescue XTZ is called
    scenario += pool.rescueXTZ(
      sp.record(
        destinationAddress = dummy.address
      )
    ).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN XTZ is transferred.
    scenario.verify(pool.balance == sp.tez(0))
    scenario.verify(dummy.balance == xtzAmount)

  ################################################################
  # setContractMetadata
  ################################################################

  @sp.add_test(name="setContractMetadata - succeeds when called by governor")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    pool = SavingsPoolContract(
      governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    )
    scenario += pool

    # WHEN the setContractMetadata is called with a new locator
    locatorKey = ""
    newLocator = sp.bytes('0x1234567890')
    scenario += pool.setContractMetadata((locatorKey, newLocator)).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    scenario.verify(pool.data.metadata[locatorKey] == newLocator)

  @sp.add_test(name="setContractMetadata - fails when not called by governor")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    pool = SavingsPoolContract(
      governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    )
    scenario += pool

    # WHEN the setContractMetadata is called by someone who isn't the governor THEN the call fails
    locatorKey = ""
    newLocator = sp.bytes('0x1234567890')
    scenario += pool.setContractMetadata((locatorKey, newLocator)).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False
    )            

  ################################################################
  # setTokenMetadata
  ################################################################

  @sp.add_test(name="setTokenMetadata - succeeds when called by governor")
  def test():
    # GIVEN a pool contract
    scenario = sp.test_scenario()

    pool = SavingsPoolContract(
      governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    )
    scenario += pool

    # WHEN the setTokenMetadata is called with a new data set.
    newKey = "new"
    newValue = sp.bytes('0x123456')
    newMap = sp.map(
      l = {
        newKey: newValue
      },
      tkey = sp.TString,
      tvalue = sp.TBytes
    )
    newData = sp.record(
      token_id = sp.nat(0),
      token_info = newMap
    )
    scenario += pool.setTokenMetadata(newData).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )

    # THEN the contract is updated.
    tokenMetadata = pool.data.token_metadata[0]
    tokenId = tokenMetadata.token_id
    tokenMetadataMap = tokenMetadata.token_info
            
    scenario.verify(tokenId == sp.nat(0))
    scenario.verify(tokenMetadataMap[newKey] == newValue)

  @sp.add_test(name="setTokenMetadata - fails when not called by governor")
  def test():
    # GIVEN a Pool contract
    scenario = sp.test_scenario()

    pool = SavingsPoolContract(
      governorContractAddress = Addresses.GOVERNOR_ADDRESS,
    )
    scenario += pool

    # WHEN the setTokenMetadata is called by someone who isn't the governor THEN the call fails
    newMap = sp.map(
      l = {
        "new": sp.bytes('0x123456')
      },
      tkey = sp.TString,
      tvalue = sp.TBytes
    )
    newData = sp.record(
      token_id = sp.nat(0),
      token_info = newMap
    )
    scenario += pool.setTokenMetadata(newData).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False
    )            

  ################################################################
  # setGovernorContract
  ################################################################

  @sp.add_test(name="setGovernorContract - fails if sender is not governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setGovernorContract is called by someone other than the governor
    # THEN the call will fail
    notGovernor = Addresses.NULL_ADDRESS
    scenario += pool.setGovernorContract(Addresses.ROTATED_ADDRESS).run(
      sender = notGovernor,
      valid = False
    )

  @sp.add_test(name="setGovernorContract - can rotate governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setGovernorContract is called
    scenario += pool.setGovernorContract(Addresses.ROTATED_ADDRESS).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )    

    # THEN the governor is rotated.
    scenario.verify(pool.data.governorContractAddress == Addresses.ROTATED_ADDRESS)

  ################################################################
  # setStabilityFundContract
  ################################################################

  @sp.add_test(name="setStabilityFundContract - fails if sender is not governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setStabilityFundContract is called by someone other than the governor
    # THEN the call will fail
    notGovernor = Addresses.NULL_ADDRESS
    scenario += pool.setStabilityFundContract(Addresses.ROTATED_ADDRESS).run(
      sender = notGovernor,
      valid = False
    )

  @sp.add_test(name="setStabilityFundContract - can rotate governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setStabilityFundContract is called
    scenario += pool.setStabilityFundContract(Addresses.ROTATED_ADDRESS).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )    

    # THEN the governor is rotated.
    scenario.verify(pool.data.stabilityFundContractAddress == Addresses.ROTATED_ADDRESS)

  ################################################################
  # setPauseGuardianContract
  ################################################################

  @sp.add_test(name="setPauseGuardianContract - fails if sender is not governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setPauseGuardianContract is called by someone other than the governor
    # THEN the call will fail
    notGovernor = Addresses.NULL_ADDRESS
    scenario += pool.setPauseGuardianContract(Addresses.ROTATED_ADDRESS).run(
      sender = notGovernor,
      valid = False,      
    )

  @sp.add_test(name="setPauseGuardianContract - can rotate pause guardian")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setPauseGuardianContract is called
    scenario += pool.setPauseGuardianContract(Addresses.ROTATED_ADDRESS).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )    

    # THEN the pause guardian is rotated.
    scenario.verify(pool.data.pauseGuardianContractAddress == Addresses.ROTATED_ADDRESS)

  ################################################################
  # setInterestRate
  ################################################################

  @sp.add_test(name="setInterestRate - fails if sender is not governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setInterestRate is called by someone other than the governor
    # THEN the call will fail
    notGovernor = Addresses.NULL_ADDRESS
    newInterestRate = sp.nat(123)
    scenario += pool.setInterestRate(newInterestRate).run(
      sender = notGovernor,
      valid = False
    )

  @sp.add_test(name="setInterestRate - accrues interest on update")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract.
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a Pool contract
    initialValue = Constants.PRECISION
    pool = SavingsPoolContract(
      interestRate = sp.nat(100000000000000000),
      underlyingBalance = initialValue,
      lastInterestCompoundTime = sp.timestamp(0)
    )
    scenario += pool

    # AND a stability fund contract.
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the pool contract is wired to the stability fund.
    scenario += pool.setStabilityFundContract(stabilityFund.address).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # AND the pool has the initial underlying balance.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = initialValue
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN the interest rate is adjusted after one period
    newInterestRate = sp.nat(123)
    scenario += pool.setInterestRate(newInterestRate).run(
      sender = Addresses.GOVERNOR_ADDRESS,
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the contract has the right number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == 1100000000000000000)

    # AND the underlying balance was updated correctly.
    scenario.verify(pool.data.underlyingBalance == 1100000000000000000)

  @sp.add_test(name="setInterestRate - updates rate")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN setInterestRate is called
    newInterestRate = sp.nat(123)
    scenario += pool.setInterestRate(newInterestRate).run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )    

    # THEN the interest rate is updated.
    scenario.verify(pool.data.interestRate == newInterestRate)

  ################################################################
  # unpause
  ################################################################

  @sp.add_test(name="unpause - fails if sender is not governor")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract which is paused
    pool = SavingsPoolContract(
      paused = True
    )
    scenario += pool

    # WHEN unpause is called by someone other than the governor
    # THEN the call will fail
    notGovernor = Addresses.NULL_ADDRESS
    scenario += pool.unpause().run(
      sender = notGovernor,
      valid = False
    )

  @sp.add_test(name="unpause - can unpause contract")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract which is paused
    pool = SavingsPoolContract(
      paused = True,
    )
    scenario += pool

    # WHEN unpause is called
    scenario += pool.unpause().run(
      sender = Addresses.GOVERNOR_ADDRESS,
    )    

    # THEN the contract is unpaused
    scenario.verify(pool.data.paused == False)

  ################################################################
  # pause
  ################################################################

  @sp.add_test(name="unpause - fails if sender is not pause guardian")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract(
      paused = True
    )
    scenario += pool

    # WHEN pause is called by someone other than the pause guardian
    # THEN the call will fail
    notPauseGuardian = Addresses.NULL_ADDRESS
    scenario += pool.unpause().run(
      sender = notPauseGuardian,
      valid = False
    )

  @sp.add_test(name="pause - can pause contract")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a pool contract
    pool = SavingsPoolContract()
    scenario += pool

    # WHEN pause is called
    scenario += pool.pause().run(
      sender = Addresses.PAUSE_GUARDIAN_ADDRESS,
    )    

    # THEN the contract is paused
    scenario.verify(pool.data.paused == True)    

  ################################################################
  # deposit
  ################################################################

  @sp.add_test(name="deposit - fails in bad state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract in the WAITING_DEPOSIT state
    pool = SavingsPoolContract(
      tokenContractAddress = token.address,
      state = WAITING_DEPOSIT
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # WHEN Alice deposits tokens in the contract.
    # THEN the call fails
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS,
      valid = False
    )

  @sp.add_test(name="deposit - resets state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN the state is reset to idle.
    scenario.verify(pool.data.state == IDLE)
    scenario.verify(pool.data.savedState_tokensToDeposit.is_some() == False)
    scenario.verify(pool.data.savedState_depositor.is_some() == False)

  @sp.add_test(name="deposit - fails when paused")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract that is paused
    pool = SavingsPoolContract(
      tokenContractAddress = token.address,
      paused = True,
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice deposits tokens in the contract
    # THEN the call fails because the contract is paused.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS,
      valid = False,
    )

  @sp.add_test(name="deposit - can deposit from one account")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice trades her tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == aliceTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens)
    scenario.verify(pool.data.underlyingBalance == aliceTokens)

  @sp.add_test(name="deposit - accrues interest on deposit")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract with an interest rate.
    initialBalance = Constants.PRECISION
    pool = SavingsPoolContract(
      interestRate = sp.nat(100000000000000000),
      lastInterestCompoundTime = sp.timestamp(0),
      underlyingBalance = initialBalance,
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND the pool has the initial number of tokens.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = initialBalance
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a stability fund contract
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 10000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the pool is wired to the stability fund.
    scenario += pool.setStabilityFundContract(stabilityFund.address).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # AND Alice has tokens
    aliceTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND BOB has tokens
    bobTokens = 20 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Alice deposits tokens in the contract after one compound period
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS,
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    )

    # THEN Alice trades her tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == aliceTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    # Expected = initial balance + interest accrued + new tokens from alice.
    expectedPoolTokensAfterAliceDeposit = aliceTokens + initialBalance + 100000000000000000
    scenario.verify(token.data.balances[pool.address].balance == expectedPoolTokensAfterAliceDeposit)
    scenario.verify(pool.data.underlyingBalance == expectedPoolTokensAfterAliceDeposit)

    # WHEN Bob deposits tokens in the contract after a second compound period.
    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS,
      now = sp.timestamp(2 * Constants.SECONDS_PER_COMPOUND)
    )

    # THEN the pool accrues interest again.
    # Expected tokens = tokens after alice deposited + 10% interest accrual + new tokens from Bob.
    expectedPoolTokensAfterBobDeposit = (expectedPoolTokensAfterAliceDeposit + (expectedPoolTokensAfterAliceDeposit // 10)) + bobTokens # Accrue interest on Alice's tokens
    scenario.verify(token.data.balances[pool.address].balance == expectedPoolTokensAfterBobDeposit)
    scenario.verify(pool.data.underlyingBalance == expectedPoolTokensAfterBobDeposit)

    # AND Bob and Alice have the right number of liquidity provider tokens
    # Pool should have       3221000000000000000 tokens
    #
    # Alice should get about 1210000000000000000 tokens:
    # = Initial + Alice Tokens + Two Compounds
    # Bob should get about   2000000000000000000 tokens:
    # = Bob Tokens
    #
    # Alice should own .379074821484011177 of the pool
    # Bob should own .620925178515988822 of the pool
    alicePoolOwnership = pool.data.balances[Addresses.ALICE_ADDRESS].balance * Constants.PRECISION / pool.data.totalSupply
    bobPoolOwnership = pool.data.balances[Addresses.BOB_ADDRESS].balance * Constants.PRECISION / pool.data.totalSupply
    scenario.verify(alicePoolOwnership == 379074821484011177)
    scenario.verify(bobPoolOwnership == 620925178515988822)

  @sp.add_test(name="deposit - can deposit from two accounts")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )
    
    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice trades her tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND Bob trades his tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4  * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == (aliceTokens + bobTokens) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens + bobTokens)
    scenario.verify(pool.data.underlyingBalance == aliceTokens + bobTokens)

  @sp.add_test(name="deposit - can deposit from two accounts - reversed")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice trades her tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND Bob trades his tokens for LP tokens
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4  * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == (aliceTokens + bobTokens) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens + bobTokens)
    scenario.verify(pool.data.underlyingBalance == aliceTokens + bobTokens)

  @sp.add_test(name="deposit - successfully mints LP tokens after additional liquidity is deposited in the pool")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie has tokens
    charlieTokens = sp.nat(60)
    scenario += token.mint(
      sp.record(
        address = Addresses.CHARLIE_ADDRESS,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND Charlie has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie joins after the liquidity is added
    scenario += pool.deposit(
      charlieTokens
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # THEN the contract doubles the number of LP tokens
    scenario.verify(pool.data.totalSupply == (100 * Constants.PRECISION))

    # AND the pool has the right number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(10 + 40 + 10 + 60))
    scenario.verify(pool.data.underlyingBalance == sp.nat(10 + 40 + 10 + 60))

    # AND Charlie has the right number of LP tokens.
    scenario.verify(pool.data.balances[Addresses.CHARLIE_ADDRESS].balance == 50 * Constants.PRECISION)

  @sp.add_test(name="deposit - successfully mints LP tokens after additional liquidity is deposited in the pool with a small amount of tokens")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie has tokens
    charlieTokens = sp.nat(20)
    scenario += token.mint(
      sp.record(
        address = Addresses.CHARLIE_ADDRESS,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND Charlie has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie joins after the liquidity is added
    scenario += pool.deposit(
      charlieTokens
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # # THEN the contract computes the LP tokens correctly
    scenario.verify(pool.data.totalSupply == (66666666666666666666))

    # AND the pool has the right number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(10 + 40 + 10 + 20))
    scenario.verify(pool.data.underlyingBalance == sp.nat(10 + 40 + 10 + 20))

    # AND Charlie has the right number of LP tokens.
    scenario.verify(pool.data.balances[Addresses.CHARLIE_ADDRESS].balance == 16666666666666666666)

  ################################################################
  # deposit_callback
  ################################################################

  @sp.add_test(name="deposit_callback - can finish deposit")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the WAITING_DEPOSIT state
    pool = SavingsPoolContract(
      state = WAITING_DEPOSIT,
      savedState_depositor = sp.some(Addresses.ALICE_ADDRESS),
      savedState_tokensToDeposit = sp.some(aliceTokens),

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN deposit_callback is run
    scenario += pool.deposit_callback(
      poolTokens
    ).run(
      sender = token.address
    )

    # THEN the call succeeds.
    # NOTE: The exact end state is covered by `deposit` tests - we just want to prove that deposit_callback works
    # under the given conditions so we can vary state and sender in other tests to prove it fails.
    scenario.verify(pool.data.state == IDLE)

  @sp.add_test(name="deposit_callback - fails in bad state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the IDLE state
    pool = SavingsPoolContract(
      state = IDLE,
      savedState_depositor = sp.none,
      savedState_tokensToDeposit = sp.none,

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN deposit_callback is run
    # THEN the call fails
    scenario += pool.deposit_callback(
      poolTokens
    ).run(
      sender = token.address,
      valid = False
    )

  @sp.add_test(name="deposit_callback - fails with bad sender")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the WAITING_DEPOSIT state
    pool = SavingsPoolContract(
      state = WAITING_DEPOSIT,
      savedState_depositor = sp.some(Addresses.ALICE_ADDRESS),
      savedState_tokensToDeposit = sp.some(aliceTokens),

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN deposit_callback is called by someone other than the token contract
    # THEN the call fails.
    scenario += pool.deposit_callback(
      poolTokens
    ).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False
    )

  ################################################################
  # redeem
  ################################################################

  @sp.add_test(name="redeem - fails in bad state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract not in the IDLE state
    pool = SavingsPoolContract(
      state = WAITING_REDEEM,
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has LP tokens
    scenario += pool.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens * Constants.PRECISION
      )
    ).run(
      sender = pool.address
    )

    # WHEN Alice withdraws from the contract
    # THEN the call fails.
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS,
      valid = False
    )

  @sp.add_test(name="redeem - clears state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )    

    # AND Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # WHEN Alice withdraws from the contract.
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN the pool's state is idle.
    scenario.verify(pool.data.state == IDLE)
    scenario.verify(pool.data.savedState_tokensToRedeem.is_some() == False)
    scenario.verify(pool.data.savedState_redeemer.is_some() == False)

  @sp.add_test(name="redeem - fails when paused")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      interestRate = sp.nat(100000000000000000),
      lastInterestCompoundTime = sp.timestamp(0),
      underlyingBalance = sp.nat(0),
      tokenContractAddress = token.address,
    )
    scenario += pool

    # AND a stability fund contract
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the pool is wired to the stability fund.
    scenario += pool.setStabilityFundContract(stabilityFund.address).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # AND Alice has tokens
    aliceTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND BOB has tokens
    bobTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens into the pool
    scenario += pool.deposit(
      aliceTokens
    ).run(
      now = sp.timestamp(1),
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      now = sp.timestamp(2),
      sender = Addresses.BOB_ADDRESS
    )

    # Sanity check, both Bob and Alice own equal chunks of the pool and the
    # pool is the sum of their tokens.
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == pool.data.balances[Addresses.BOB_ADDRESS].balance)
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens + bobTokens)

    # AND the pool is paused
    scenario += pool.pause().run(
      sender = Addresses.PAUSE_GUARDIAN_ADDRESS,
    )
    
    # WHEN Alice withdraws her tokens after one compound period
    # THEN the call fails because the pool is paused.
    scenario += pool.redeem(
      pool.data.balances[Addresses.ALICE_ADDRESS].balance 
    ).run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND),
      sender = Addresses.ALICE_ADDRESS, 
      valid = False,
    )

  @sp.add_test(name="redeem - accrues interest on redeem")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract with an interest rate.
    pool = SavingsPoolContract(
      interestRate = sp.nat(100000000000000000),
      lastInterestCompoundTime = sp.timestamp(0),
      underlyingBalance = sp.nat(0),
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND a stability fund contract
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the pool is wired to the stability fund.
    scenario += pool.setStabilityFundContract(stabilityFund.address).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # AND Alice has tokens
    aliceTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND BOB has tokens
    bobTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens into the pool
    scenario += pool.deposit(
      aliceTokens
    ).run(
      now = sp.timestamp(1),
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      now = sp.timestamp(2),
      sender = Addresses.BOB_ADDRESS
    )

    # Sanity check, both Bob and Alice own equal chunks of the pool and the
    # pool is the sum of their tokens.
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == pool.data.balances[Addresses.BOB_ADDRESS].balance)
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens + bobTokens)

    # WHEN Alice withdraws her tokens after one compound period
    scenario += pool.redeem(
      pool.data.balances[Addresses.ALICE_ADDRESS].balance 
    ).run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND),
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice's LP tokens are burn and she receives one half of the interest payment. 
    poolBalance = aliceTokens + bobTokens
    interestPayment = poolBalance // 10
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens + (interestPayment / 2))

    # AND the pool tracks the balance correctly. 
    expectedRemainingTokensAfterAliceRedemption = bobTokens + (interestPayment / 2)
    scenario.verify(pool.data.underlyingBalance == expectedRemainingTokensAfterAliceRedemption)
    scenario.verify(token.data.balances[pool.address].balance == expectedRemainingTokensAfterAliceRedemption)

    # WHEN Bob withdraws his tokens/
    scenario += pool.redeem(
      pool.data.balances[Addresses.BOB_ADDRESS].balance
    ).run(
      now = sp.timestamp(Constants.SECONDS_PER_COMPOUND + 1),
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Bob's LP tokens are burnt and he receives all the remaining tokens
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens + (interestPayment / 2))

    # AND the pool tracks the balance correctly. 
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))

  @sp.add_test(name="redeem - can empty when accruing")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract with an interest rate.
    pool = SavingsPoolContract(
      interestRate = sp.nat(100000000000000000),
      lastInterestCompoundTime = sp.timestamp(0),
      underlyingBalance = sp.nat(0),
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND a stability fund contract
    stabilityFund = StabilityFund.StabilityFundContract(
      savingsAccountContractAddress = pool.address,
      tokenContractAddress = token.address,
    )
    scenario += stabilityFund

    # AND the stability fund has many tokens
    scenario += token.mint(
      sp.record(
        address = stabilityFund.address,
        value = 1000000000000 * Constants.PRECISION
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND the pool is wired to the stability fund.
    scenario += pool.setStabilityFundContract(stabilityFund.address).run(
      sender = Addresses.GOVERNOR_ADDRESS
    )

    # AND Alice has tokens
    aliceTokens = 10 * Constants.PRECISION  
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )    

    # AND Alice tokens into the pool
    scenario += pool.deposit(
      aliceTokens
    ).run(
      now = sp.timestamp(1),
      sender = Addresses.ALICE_ADDRESS
    )

    # WHEN alice calls withdraw
    # THEN it will succeed.
    now = sp.timestamp(Constants.SECONDS_PER_COMPOUND)
    scenario += pool.redeem(
      pool.data.balances[Addresses.ALICE_ADDRESS].balance 
    ).run(
      now = now,
      sender = Addresses.ALICE_ADDRESS,
    )

    # AND Alice's LP tokens are burn and she receives the interest payment. 
    interestPayment = aliceTokens // 10
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens + interestPayment)

    # AND the pool tracks the balance correctly. 
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))

  @sp.add_test(name="redeem - can deposit and withdraw from one account")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # WHEN Alice withdraws from the contract.
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice trades her LP tokens for her original tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="redeem - can redeem from two accounts")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Alice withdraws her tokens
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == bobTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens)
    scenario.verify(pool.data.underlyingBalance == bobTokens)

    # WHEN Bob withdraws his tokens
    scenario += pool.redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="redeem - can redeem from two accounts - reversed")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Bob withdraws his tokens
    scenario += pool.redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == aliceTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens)
    scenario.verify(pool.data.underlyingBalance == aliceTokens)

    # WHEN Alice withdraws her tokens
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="redeem - can redeem partially from two accounts")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Alice withdraws half of her tokens
    scenario += pool.redeem(
      aliceTokens / 2 * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2 * Constants.PRECISION)

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == (bobTokens + (aliceTokens / 2)) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens + (aliceTokens / 2))
    scenario.verify(pool.data.underlyingBalance == bobTokens + (aliceTokens / 2))

    # WHEN Bob withdraws a quarter of his tokens
    scenario += pool.redeem(
      bobTokens / 4 * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2 * Constants.PRECISION)

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == 9) # Bob withdraws 22% (10/45) of the pool, which is 9.9999 tokens. Integer math truncates the remainder
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == 30 * Constants.PRECISION) # Bob withdrew 1/4 of tokens = .25 * 40 = 30

    # AND the total supply of tokens is as expected
    # Expected = 50 tokens generated - 5 tokens alice redeemed - 10 tokens bob redeemed
    scenario.verify(pool.data.totalSupply == sp.nat(35) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    # Expected:
    # 1/2 of alice tokens + 3/4 of bob tokens + 1 token rounding error = 5 + 30 + 1 = 36
    expectedRemainingTokens = sp.nat(36)
    scenario.verify(token.data.balances[pool.address].balance == expectedRemainingTokens) 
    scenario.verify(pool.data.underlyingBalance == expectedRemainingTokens)

  @sp.add_test(name="redeem - can redeem from two accounts with liquidity added")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )    

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice withdraws her tokens
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens plus a proportion of the additional tokens back and the LP tokens are burnt
    # Alice owns 20% of the pool * 10 additional tokens = 2 additional tokens
    additionalTokensForAlice = sp.nat(2)
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens + additionalTokensForAlice)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == bobTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    # 10 tokens were added to the pool - 2 tokens alice withdrew = 8 additional tokens remaining.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens + sp.as_nat(additionalTokens - additionalTokensForAlice))
    scenario.verify(pool.data.underlyingBalance == bobTokens + sp.as_nat(additionalTokens - additionalTokensForAlice))

    # WHEN Bob withdraws his tokens
    scenario += pool.redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens + additionalTokensForAlice)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob receives his original tokens back and the LP tokens are burn.
    # Bob owned 80% of the pool * 10 additional tokens = 8 additional tokens   
    additionalTokensForBob = sp.nat(8)
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens + additionalTokensForBob)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="redeem - can redeem correctly from accounts joining after liquidity is added")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie has tokens
    charlieTokens = sp.nat(60)
    scenario += token.mint(
      sp.record(
        address = Addresses.CHARLIE_ADDRESS,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND Charlie has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie joins after the liquidity is added
    scenario += pool.deposit(
      charlieTokens
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # WHEN everyone withdraws their tokens
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )
    
    scenario += pool.redeem(
      pool.data.balances[Addresses.CHARLIE_ADDRESS].balance
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # THEN all LP tokens are burnt
    scenario.verify(pool.data.totalSupply == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.CHARLIE_ADDRESS].balance == sp.nat(0))

    # AND the pool has no tokens left in it.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

    # AND Balances are expected
    # NOTE: there are minor rounding errors on withdrawals.
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(12))
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(47))
    scenario.verify(token.data.balances[Addresses.CHARLIE_ADDRESS].balance == sp.nat(61))

  @sp.add_test(name="redeem - can redeem correctly from accounts joining after liquidity is added with fraction of pool")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie has tokens
    charlieTokens = sp.nat(20)
    scenario += token.mint(
      sp.record(
        address = Addresses.CHARLIE_ADDRESS,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND Charlie has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = charlieTokens
      )
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Charlie joins after the liquidity is added
    scenario += pool.deposit(
      charlieTokens
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # WHEN everyone withdraws their tokens
    scenario += pool.redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )
    
    scenario += pool.redeem(
      pool.data.balances[Addresses.CHARLIE_ADDRESS].balance
    ).run(
      sender = Addresses.CHARLIE_ADDRESS
    )

    # THEN all LP tokens are burnt
    scenario.verify(pool.data.totalSupply == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.CHARLIE_ADDRESS].balance == sp.nat(0))

    # AND the pool has no tokens left in it.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

    # AND Balances are expected
    # NOTE: there are minor rounding errors on withdrawals.
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(12))
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(47))
    scenario.verify(token.data.balances[Addresses.CHARLIE_ADDRESS].balance == sp.nat(21))

  ################################################################
  # redeem_callback
  ################################################################

  @sp.add_test(name="redeem_callback - can finish redeem")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the WAITING_REDEEM state
    pool = SavingsPoolContract(
      state = WAITING_REDEEM,
      savedState_redeemer = sp.some(Addresses.ALICE_ADDRESS),
      savedState_tokensToRedeem = sp.some(aliceTokens * Constants.PRECISION),

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has LP tokens
    scenario += pool.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens * Constants.PRECISION
      )
    ).run(
      sender = pool.address
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN redeem_callback is run
    scenario += pool.redeem_callback(
      poolTokens
    ).run(
      sender = token.address
    )

    # THEN the call succeeds.
    # NOTE: The exact end state is covered by `redeem` tests - we just want to prove that redeem_callback works
    # under the given conditions so we can vary state and sender in other tests to prove it fails.
    scenario.verify(pool.data.state == IDLE)

  @sp.add_test(name="redeem_callback - fails in bad state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the IDLE state
    pool = SavingsPoolContract(
      state = IDLE,
      savedState_redeemer = sp.none,
      savedState_tokensToRedeem = sp.none,

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has LP tokens
    scenario += pool.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens * Constants.PRECISION
      )
    ).run(
      sender = pool.address
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN redeem_callback is run
    # THEN the call fails
    scenario += pool.redeem_callback(
      poolTokens
    ).run(
      sender = token.address,
      valid = False
    )

  @sp.add_test(name="redeem_callback - fails with bad sender")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND a pool contract in the WAITING_REDEEM state
    pool = SavingsPoolContract(
      state = WAITING_REDEEM,
      savedState_redeemer = sp.some(Addresses.ALICE_ADDRESS),
      savedState_tokensToRedeem = sp.some(aliceTokens * Constants.PRECISION),

      tokenContractAddress = token.address
    )
    scenario += pool
    
    # AND Alice has LP tokens
    scenario += pool.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens * Constants.PRECISION
      )
    ).run(
      sender = pool.address
    )

    # AND the pool has tokens
    poolTokens = Constants.PRECISION * 200
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = poolTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN redeem_callback is run from someone other than the token contract
    # THEN the call fails.
    scenario += pool.redeem_callback(
      poolTokens
    ).run(
      sender = Addresses.NULL_ADDRESS,
      valid = False
    )

  ################################################################
  # UNSAFE_redeem
  ################################################################

  @sp.add_test(name="UNSAFE_redeem - fails in bad state")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract not in the IDLE state
    pool = SavingsPoolContract(
      state = WAITING_REDEEM,
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has LP tokens
    scenario += pool.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens * Constants.PRECISION
      )
    ).run(
      sender = pool.address
    )

    # WHEN Alice withdraws from the contract
    # THEN the call fails.
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS,
      valid = False
    )

  @sp.add_test(name="UNSAFE_redeem - can deposit and withdraw from one account when paused")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND the pool is paused
    scenario += pool.pause().run(
      sender = Addresses.PAUSE_GUARDIAN_ADDRESS,
    )

    # WHEN Alice withdraws from the contract.
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice trades her LP tokens for her original tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="UNSAFE_redeem - can deposit and withdraw from one account")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice deposits tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # WHEN Alice withdraws from the contract.
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice trades her LP tokens for her original tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="UNSAFE_redeem - can redeem from two accounts")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Alice withdraws her tokens
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == bobTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens)
    scenario.verify(pool.data.underlyingBalance == bobTokens)

    # WHEN Bob withdraws his tokens
    scenario += pool.UNSAFE_redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="UNSAFE_redeem - can redeem from two accounts - reversed")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Bob withdraws his tokens
    scenario += pool.UNSAFE_redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens * Constants.PRECISION)

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == aliceTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == aliceTokens)
    scenario.verify(pool.data.underlyingBalance == aliceTokens)

    # WHEN Alice withdraws her tokens
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(0))
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  @sp.add_test(name="UNSAFE_redeem - can redeem partially from two accounts")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # WHEN Alice withdraws half of her tokens
    scenario += pool.UNSAFE_redeem(
      aliceTokens / 2 * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives her original tokens back and the LP tokens are burnt
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2 * Constants.PRECISION)

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == (bobTokens + (aliceTokens / 2)) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens + (aliceTokens / 2))
    scenario.verify(pool.data.underlyingBalance == bobTokens + (aliceTokens / 2))

    # WHEN Bob withdraws a quarter of his tokens
    scenario += pool.UNSAFE_redeem(
      bobTokens / 4 * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens / 2 * Constants.PRECISION)

    # AND Bob receives his original tokens back and the LP tokens are burn.
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == 9) # Bob withdraws 22% (10/45) of the pool, which is 9.9999 tokens. Integer math truncates the remainder
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == 30 * Constants.PRECISION) # Bob withdrew 1/4 of tokens = .25 * 40 = 30

    # AND the total supply of tokens is as expected
    # Expected = 50 tokens generated - 5 tokens alice redeemed - 10 tokens bob redeemed
    scenario.verify(pool.data.totalSupply == sp.nat(35) * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    # Expected:
    # 1/2 of alice tokens + 3/4 of bob tokens + 1 token rounding error = 5 + 30 + 1 = 36
    expectedRemainingTokens = sp.nat(36)
    scenario.verify(token.data.balances[pool.address].balance == expectedRemainingTokens) 
    scenario.verify(pool.data.underlyingBalance == expectedRemainingTokens)

  @sp.add_test(name="UNSAFE_redeem - can redeem from two accounts with liquidity added")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a token contract
    token = Token.FA12(
      admin = Addresses.TOKEN_ADMIN_ADDRESS
    )
    scenario += token

    # AND a pool contract
    pool = SavingsPoolContract(
      tokenContractAddress = token.address
    )
    scenario += pool

    # AND Alice has tokens
    aliceTokens = sp.nat(10)
    scenario += token.mint(
      sp.record(
        address = Addresses.ALICE_ADDRESS,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Bob has twice as many tokens
    bobTokens = sp.nat(40)
    scenario += token.mint(
      sp.record(
        address = Addresses.BOB_ADDRESS,
        value = bobTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = aliceTokens
      )
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # AND Bob has given the pool an allowance
    scenario += token.approve(
      sp.record(
        spender = pool.address,
        value = bobTokens
      )
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # And the pool is initialized to a zero balance in the token contract
    # NOTE: This is a workaround for a bug in the kUSD contract where `getBalance` will failwith if called for an address that wasn't
    #       previously initialized.
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = 0
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # AND Alice and Bob deposit tokens in the contract.
    scenario += pool.deposit(
      aliceTokens
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    scenario += pool.deposit(
      bobTokens
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # AND the contract receives an additional number of tokens.
    additionalTokens = 10
    scenario += token.mint(
      sp.record(
        address = pool.address,
        value = additionalTokens
      )
    ).run(
      sender = Addresses.TOKEN_ADMIN_ADDRESS
    )

    # WHEN Alice withdraws her tokens
    scenario += pool.UNSAFE_redeem(
      aliceTokens * Constants.PRECISION
    ).run(
      sender = Addresses.ALICE_ADDRESS
    )

    # THEN Alice receives only her original tokens
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob still has his position
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == aliceTokens * 4 * Constants.PRECISION)

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == bobTokens * Constants.PRECISION)

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == bobTokens + additionalTokens)

    # AND the pool has not yet balanced the additional tokens
    scenario.verify(pool.data.underlyingBalance == bobTokens)

    # WHEN Bob withdraws his tokens
    scenario += pool.UNSAFE_redeem(
      bobTokens * Constants.PRECISION
    ).run(
      sender = Addresses.BOB_ADDRESS
    )

    # THEN Alice retains her position
    scenario.verify(token.data.balances[Addresses.ALICE_ADDRESS].balance == aliceTokens)
    scenario.verify(pool.data.balances[Addresses.ALICE_ADDRESS].balance == sp.nat(0))

    # AND Bob receives his original tokens back
    scenario.verify(token.data.balances[Addresses.BOB_ADDRESS].balance == bobTokens)
    scenario.verify(pool.data.balances[Addresses.BOB_ADDRESS].balance == sp.nat(0))

    # AND the total supply of tokens is as expected
    scenario.verify(pool.data.totalSupply == sp.nat(0))

    # AND the pool has possession of the correct number of tokens.
    scenario.verify(token.data.balances[pool.address].balance == sp.nat(10))

    # AND the pool thinks it has 0 tokens
    scenario.verify(pool.data.underlyingBalance == sp.nat(0))

  ################################################################
  # offchainView_poolSize
  ################################################################

  @sp.add_test(name="offchainView_poolSize - calculates values correctly")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract
    interestRate = sp.nat(100000000000000000)
    initialValue = Constants.PRECISION
    lastInterestCompoundTime = sp.timestamp(0)
    pool = SavingsPoolContract(
      interestRate = interestRate,
      underlyingBalance = initialValue,
      lastInterestCompoundTime = lastInterestCompoundTime,
    )
    scenario += pool

    # AND some the expected values after one and two interest periods
    # NOTE: Compounding is done via linear approximation:
    #   Expected = (initial_value * (1 + (number_periods * interest_rate)))
    expectedValueAfterOnePeriod = 1100000000000000000  # = (1 * (1 + (1 * .10))) * PRECISION
    expectedValueAfterTwoPeriods = 1200000000000000000 # = (1 * (1 + (2 * .10))) * PRECISION

    # WHEN the view is called
    # THEN then the initial value is returned
    scenario.verify(pool.offchainView_poolSize() == initialValue)

    # WHEN the view is called after one period
    # THEN the view returns one period of compounding
    # TODO (keefertaylor): Enable this when SmartPy supports it. See: https://t.me/SmartPy_io/17555
    # scenario.verify(pool.offchainView_poolSize() == expectedValueAfterOnePeriod)

    # WHEN the view is called after two periods
    # THEN the view returns two periods of compounding
    # TODO (keefertaylor): Enable this when SmartPy supports it. See: https://t.me/SmartPy_io/17555
    # scenario.verify(pool.offchainView_poolSize() == expectedValueAfterTwoPeriods)

    # WHEN the view is called after two and a half periods
    # THEN the view correctly floors and returns two periods of compounding
    # TODO (keefertaylor): Enable this when SmartPy supports it. See: https://t.me/SmartPy_io/17555
    # scenario.verify(pool.offchainView_poolSize() == expectedValueAfterTwoPeriods)

  ################################################################
  # offchainView_poolSize
  ################################################################

  @sp.add_test(name="offchainView_getLPTokenConversionRate - Calculates conversion rate with one LP token issued")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 100 kUSD and 1 LP token issued
    pool = SavingsPoolContract(
      underlyingBalance = 100 * Constants.PRECISION,
      totalSupply = 1 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN the conversion rate is 1 LP token = 100 kUSD
    scenario.verify(pool.offchainView_getLPTokenConversionRate() == 100 * Constants.PRECISION)

  @sp.add_test(name="offchainView_getLPTokenConversionRate - Calculates conversion rate with many LP tokens issued")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 100 kUSD and 5 LP token issued
    pool = SavingsPoolContract(
      underlyingBalance = 100 * Constants.PRECISION,
      totalSupply = 5 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN the conversion rate is 1 LP token = 20 kUSD (100 kUSD / 5 LP tokens)
    scenario.verify(pool.offchainView_getLPTokenConversionRate() == 20 * Constants.PRECISION)

  @sp.add_test(name="offchainView_getLPTokenConversionRate - Calculates conversion rate when conversion rate is less than 1")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 1 kUSD and 100 LP tokens issued
    pool = SavingsPoolContract(
      underlyingBalance = 1 * Constants.PRECISION,
      totalSupply = 100 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN the conversion rate is 1 LP token = .01 kUSD
    scenario.verify(pool.offchainView_getLPTokenConversionRate() == Constants.PRECISION // 100)

  @sp.add_test(name="offchainView_getLPTokenConversionRate - Calculates conversion rate with 0 LP tokens")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 1 kUSD and 0 LP tokens issued
    pool = SavingsPoolContract(
      underlyingBalance = 1 * Constants.PRECISION,
      totalSupply = 0,
    )
    scenario += pool

    # THEN the conversion rate is 0
    scenario.verify(pool.offchainView_getLPTokenConversionRate() == 0)    

  # NOTE: This can logically never happen (if there are LP tokens there should be kUSD). 
  @sp.add_test(name="offchainView_getLPTokenConversionRate - Calculates conversion rate with 0 kUSD tokens")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 10 kUSD and 1 LP tokens issued
    pool = SavingsPoolContract(
      underlyingBalance = 0,
      totalSupply = 1 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN the conversion rate is 0
    scenario.verify(pool.offchainView_getLPTokenConversionRate() == 0)   

  ################################################################
  # offchainView_getAccountValue
  ################################################################

  @sp.add_test(name="offchainView_getAccountValue - Calculates account value with one token issued")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 100 kUSD and 1 LP tokens issued to Alice
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 1 * Constants.LP_TOKEN_PRECISION)
        }
      ),
      underlyingBalance = 100 * Constants.PRECISION,      
      totalSupply = 1 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN her account value is 100
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 100 * Constants.PRECISION)   

  @sp.add_test(name="offchainView_getAccountValue - Calculates account value with many token issued")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 100 kUSD and 5 LP tokens issued to Alice
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 5 * Constants.LP_TOKEN_PRECISION)
        }
      ),
      underlyingBalance = 100 * Constants.PRECISION,      
      totalSupply = 5 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN her account value is 100
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 100 * Constants.PRECISION)   

  @sp.add_test(name="offchainView_getAccountValue - Calculates account value with multiple holders having multiple tokens")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 100 kUSD and 1 LP tokens issued to Alice, and 3 issued to Bob (4 total)
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 1 * Constants.LP_TOKEN_PRECISION),
          Addresses.BOB_ADDRESS: sp.record(approvals = {}, balance = 3 * Constants.LP_TOKEN_PRECISION)
        }
      ),
      underlyingBalance = 100 * Constants.PRECISION,      
      totalSupply = 4 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN Alice has 25 kUSD in value (100 underlying / 4 LP tokens * 1 LP token owned by Alice)
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 25 * Constants.PRECISION)       
    
    # AND Bob has 75 kUSD in value (100 underlying / 4 LP tokens * 3 LP tokens owned by Bob)
    scenario.verify(pool.offchainView_getAccountValue(Addresses.BOB_ADDRESS) == 75 * Constants.PRECISION)
  
  @sp.add_test(name="offchainView_getAccountValue - Calculates account value with multiple holders having multiple tokens when conversion rate is less than 1")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with 1 kUSD and 100 LP tokens issued to Alice, and 300 issued to Bob (400 total)
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 100 * Constants.LP_TOKEN_PRECISION),
          Addresses.BOB_ADDRESS: sp.record(approvals = {}, balance = 300 * Constants.LP_TOKEN_PRECISION)
        }
      ),
      underlyingBalance = 1 * Constants.PRECISION,      
      totalSupply = 400 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN Alice has .25 kUSD in value (1 underlying / 400 LP tokens * 100 LP token owned by Alice)
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 25 * Constants.PRECISION // 100)       
    
    # AND Bob has .75 kUSD in value (1 underlying / 400 LP tokens * 300 LP tokens owned by Bob)
    scenario.verify(pool.offchainView_getAccountValue(Addresses.BOB_ADDRESS) == 75 * Constants.PRECISION // 100)

  @sp.add_test(name="offchainView_getAccountValue - Calculates account value when no LP tokoens are issued")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with no LP tokens issued
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 0),
          Addresses.BOB_ADDRESS: sp.record(approvals = {}, balance = 0)
        }
      ),
      underlyingBalance = 100 * Constants.PRECISION,      
      totalSupply = 0,
    )
    scenario += pool

    # THEN Alice's account value is reported as 0
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 0)       
   
  # NOTE: This can logically never happen (if there are LP tokens there should be kUSD). 
  @sp.add_test(name="offchainView_getAccountValue - Calculates conversion rate with 0 kUSD tokens")
  def test():
    scenario = sp.test_scenario()

    # GIVEN a Pool contract with no kUSD and 1 LP tokens issued to Alice, and 3 issued to Bob (4 total)
    pool = SavingsPoolContract(
      balances = sp.big_map(
        l = {
          Addresses.ALICE_ADDRESS: sp.record(approvals = {}, balance = 1 * Constants.LP_TOKEN_PRECISION),
          Addresses.BOB_ADDRESS: sp.record(approvals = {}, balance = 3 * Constants.LP_TOKEN_PRECISION)
        }
      ),
      underlyingBalance = 0,      
      totalSupply = 4 * Constants.LP_TOKEN_PRECISION,
    )
    scenario += pool

    # THEN both Alice and Bob have no account value.
    scenario.verify(pool.offchainView_getAccountValue(Addresses.ALICE_ADDRESS) == 0 * Constants.PRECISION)       
    scenario.verify(pool.offchainView_getAccountValue(Addresses.BOB_ADDRESS) == 0 * Constants.PRECISION) 


  sp.add_compilation_target("savings-pool", SavingsPoolContract())
