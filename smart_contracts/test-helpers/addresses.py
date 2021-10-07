import smartpy as sp

# This file contains addresses for tests which are named and ensure uniqueness across the test suite.

# The address which acts as the Governor
GOVERNOR_ADDRESS = sp.address("tz1abmz7jiCV2GH2u81LRrGgAFFgvQgiDiaf")

# The address which acts as the OvenProxy.
OVEN_PROXY_ADDRESS = sp.address("tz1c461F8GirBvq5DpFftPoPyCcPR7HQM6gm")

# The address which acts as the OvenRegistry
OVEN_REGISTRY_ADDRESS = sp.address("tz1hAYfexyzPGG6RhZZMpDvAHifubsbb6kgn")

# The address which acts as the OvenFactory
OVEN_FACTORY_ADDRESS = sp.address("tz1irJKkXS2DBWkU1NnmFQx1c1L7pbGg4yhk")

# The address which acts as an Oven
OVEN_ADDRESS = sp.address("tz1LmaFsWRkjr7QMCx5PtV6xTUz3AmEpKQiF")

# The address which owns an Oven
OVEN_OWNER_ADDRESS = sp.address("tz1S8MNvuFEUsWgjHvi3AxibRBf388NhT1q2")

# The address of an entity which performs a liquidation.
LIQUIDATOR_ADDRESS = sp.address("tz1LcuQHNVQEWP2fZjk1QYZGNrfLDwrT3SyZ")

# The address that acts as the token contract.
TOKEN_ADDRESS = sp.address("tz1cYufsxHXJcvANhvS55h3aY32a9BAFB494")

# The address which acts as the Oracle.
ORACLE_ADDRESS = sp.address("tz1P2Po7YM526ughEsRbY4oR9zaUPDZjxFrb")

# The address wich acts as a Minter.
MINTER_ADDRESS = sp.address("tz1UUgPwikRHW1mEyVZfGYy6QaxrY6Y7WaG5")

# An address which represents a Harbinger Oracle.
HARBINGER_ADDRESS = sp.address("tz1TDSmoZXwVevLTEvKCTHWpomG76oC9S2fJ")

# An address which acts as a Fund Administrator.
FUND_ADMINISTRATOR_ADDRESS = sp.address("tz1VmiY38m3y95HqQLjMwqnMS7sdMfGomzKi")

# An address which acts as a Stability Fund.
STABILITY_FUND_ADDRESS = sp.address("tz1W5VkdB5s7ENMESVBtwyt9kyvLqPcUczRT")

# An address which acts as a Developer Fund
DEVELOPER_FUND_ADDRESS =sp.address("tz1R6Ej25VSerE3MkSoEEeBjKHCDTFbpKuSX")

# An address which can be rotated.
ROTATED_ADDRESS = sp.address("tz1UMCB2AHSTwG7YcGNr31CqYCtGN873royv")

# An address which acts as a pause guardian.
PAUSE_GUARDIAN_ADDRESS = sp.address("tz1LLNkQK4UQV6QcFShiXJ2vT2ELw449MzAA")

# An address which is never used. This is a `null` value for addresses.
NULL_ADDRESS = sp.address("tz1bTpviNnyx2PXsNmGpCQTMQsGoYordkUoA")

# The address which acts as the liquidity pool
LIQUIDITY_POOL_ADDRESS = sp.address("tz3QSGPoRp3Kn7n3vY24eYeu3Peuqo45LQ4D")

# The address of the savings account.
SAVINGS_ACCOUNT_ADDRESS = sp.address("tz1gfArv665EUkSg2ojMBzcbfwuPxAvqPvjo")

# The address which acts as the Token Admin
TOKEN_ADMIN_ADDRESS = sp.address("tz1eEnQhbwf6trb8Q8mPb2RaPkNk2rN7BKi8")

# An series of named addresses with no particular role.
# These are used for token transfer tests.
ALICE_ADDRESS = sp.address("tz1VQnqCCqX4K5sP3FNkVSNKTdCAMJDd3E1n")
BOB_ADDRESS = sp.address("tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93")
CHARLIE_ADDRESS = sp.address("tz3S6BBeKgJGXxvLyZ1xzXzMPn11nnFtq5L9")