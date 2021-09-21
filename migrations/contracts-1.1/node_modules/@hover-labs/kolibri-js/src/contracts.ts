/**
 * A property bag of known canonical contracts.
 */

import { Contracts } from './types/contracts'

import MAINNET from './contracts/mainnet'
import GRANADANET from './contracts/granadanet'
import SANDBOXNET from './contracts/sandbox'

const CONTRACTS: Contracts = {
  ZERO: GRANADANET,
  TEST: GRANADANET,
  MAIN: MAINNET,
  SANDBOX: SANDBOXNET,
}

export default CONTRACTS
