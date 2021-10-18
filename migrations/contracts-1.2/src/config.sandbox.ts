import { NetworkConfig } from '@hover-labs/tezos-utils'
import { CONTRACTS } from '@hover-labs/kolibri-js'
import BigNumber from "bignumber.js";

export const NETWORK_CONFIG: NetworkConfig = {
  name: 'Sandboxnet',
  tezosNodeUrl: 'https://sandbox.hover.engineering/',
  betterCallDevUrl: 'https://bcd.hover.engineering/v1',
  requiredConfirmations: 2,
  maxConfirmationPollingRetries: 10,
  operationDelaySecs: 10,
  contracts: CONTRACTS.SANDBOX,

  escrowAmount: 3000000000000000000000,
  governanceVoteLength: 15,
  governanceTimelockLength: 11,
}

export const MIGRATION_CONFIG = {
  // TODO(keefertaylor): Set this to a real value once we decide what it is.
  initialInterestRate: new BigNumber('1')
}