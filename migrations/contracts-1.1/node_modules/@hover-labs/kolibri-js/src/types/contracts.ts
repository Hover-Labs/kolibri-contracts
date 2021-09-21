export type DeployedContractAddressOrNull = string | null

export type ContractGroup = {
  MINTER: DeployedContractAddressOrNull
  OVEN_PROXY: DeployedContractAddressOrNull
  OVEN_FACTORY: DeployedContractAddressOrNull
  TOKEN: DeployedContractAddressOrNull
  OVEN_REGISTRY: DeployedContractAddressOrNull
  DEVELOPER_FUND: DeployedContractAddressOrNull
  STABILITY_FUND: DeployedContractAddressOrNull
  ORACLE: DeployedContractAddressOrNull

  // Dependent contracts
  HARBINGER_NORMALIZER: DeployedContractAddressOrNull

  // Kolibri Liqiudity Pool
  LIQUIDITY_POOL: DeployedContractAddressOrNull

  // DEX Configurations
  DEXES: {
    QUIPUSWAP: {
      POOL: DeployedContractAddressOrNull
      FA1_2_FACTORY: DeployedContractAddressOrNull
      FA2_FACTORY: DeployedContractAddressOrNull
    }
    PLENTY: {
      POOL: DeployedContractAddressOrNull
      PLENTY_QUIPUSWAP_POOL: DeployedContractAddressOrNull
      PLENTY_TOKEN: DeployedContractAddressOrNull
    }
  }

  // Below values are not applicable to testnet deployment.
  KOLIBRI_BAKER: DeployedContractAddressOrNull

  // Governance Roles
  GOVERNOR: DeployedContractAddressOrNull
  PAUSE_GUARDIAN: DeployedContractAddressOrNull
  BREAK_GLASS_MULTISIG: DeployedContractAddressOrNull
  FUND_ADMIN: DeployedContractAddressOrNull

  // DAO
  DAO: DeployedContractAddressOrNull
  DAO_TOKEN: DeployedContractAddressOrNull
  DAO_COMMUNITY_FUND: DeployedContractAddressOrNull

  // Farm Stuff
  FARMS: {
    KUSD: {
      farm: DeployedContractAddressOrNull
      reserve: DeployedContractAddressOrNull
    }
    QLKUSD: {
      farm: DeployedContractAddressOrNull
      reserve: DeployedContractAddressOrNull
    }
    KUSD_LP: {
      farm: DeployedContractAddressOrNull
      reserve: DeployedContractAddressOrNull
    }
  }

  VESTING_CONTRACTS: { [key: string]: DeployedContractAddressOrNull }

  BREAK_GLASS_CONTRACTS: {
    MINTER: DeployedContractAddressOrNull
    OVEN_PROXY: DeployedContractAddressOrNull
    OVEN_FACTORY: DeployedContractAddressOrNull
    TOKEN: DeployedContractAddressOrNull
    OVEN_REGISTRY: DeployedContractAddressOrNull
    DEVELOPER_FUND: DeployedContractAddressOrNull
    STABILITY_FUND: DeployedContractAddressOrNull
    ORACLE: DeployedContractAddressOrNull
    LIQUIDITY_POOL: DeployedContractAddressOrNull
    DAO_COMMUNITY_FUND: DeployedContractAddressOrNull
    VESTING_VAULTS: {
      [key: string]: DeployedContractAddressOrNull
    }
  }
}

export type Contracts = {
  ZERO: ContractGroup
  TEST: ContractGroup
  MAIN: ContractGroup
  SANDBOX: ContractGroup
}
