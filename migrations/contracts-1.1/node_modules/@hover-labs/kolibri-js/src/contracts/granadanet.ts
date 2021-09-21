import { ContractGroup } from '../types/contracts'

const contracts: ContractGroup = {
  MINTER: 'KT1VbxEqFMijFsMoL5v3u2fhLPWVWPH3jP8H',
  OVEN_PROXY: 'KT1NxrySajZEbDEdoDa6rG4YL4jvAatzdDrs',
  OVEN_FACTORY: 'KT1SyzcYyaA8wp7JoZzxMZtB7ugvK3XvFF1V',
  TOKEN: 'KT1VKtbg6piYE3GowALFN6P8MFQF3MMZT44j',
  OVEN_REGISTRY: 'KT1Ez2RCnrXYK1ffrhpJAZuiJPy971HaZmYg',
  DEVELOPER_FUND: 'KT1AzhPYRh5nAUJ9Bcor4GVWPcwXidfstmua',
  STABILITY_FUND: 'KT1Kixna8UhDjwFqSV4sfbS4J5fSnqcJc8YS',
  ORACLE: 'KT1KAgw6myNA9iH3AAg1P5BtztWeAGguGTSr',
  HARBINGER_NORMALIZER: 'KT1AQuWowr3WKwF69oTGcKaJrMajic3CKwR2',

  LIQUIDITY_POOL: 'KT1Fk7oJvpjtKga11TiYxMsuePD89UTDmUUF',

  DEXES: {
    QUIPUSWAP: {
      POOL: 'KT1BatFVF1vchbxANDJRVccKEdYppqe58Pxg',
      FA1_2_FACTORY: 'KT1EmfR5bSZN7mWgapE8FZKdbJ3NLjDHGZmd',
      FA2_FACTORY: null,
    },
    PLENTY: {
      POOL: null,
      PLENTY_QUIPUSWAP_POOL: null,
      PLENTY_TOKEN: null,
    },
  },

  KOLIBRI_BAKER: 'tz1burnburnburnburnburnburnburjAYjjX',

  GOVERNOR: 'KT1AqANbbQwdrSrAX5aDrZpwhQCX8mFoX6Si',
  PAUSE_GUARDIAN: 'KT1Qzm95Cd9C6CmAfwVKLCp5rxkwC2G9pi1k',
  BREAK_GLASS_MULTISIG: 'KT1VqdBh1iHcQj5BMsi5XpnTSqQpLtLDWTKe',
  FUND_ADMIN: null,

  DAO: 'KT1XXaDPnHktNboNpAxP7YsFs1Bhye5rgjZ5',
  DAO_TOKEN: 'KT1LDn9Mh3Y8MxMHDFtnG4q1BQVeTMNbgfgq',
  DAO_COMMUNITY_FUND: 'KT1CmS2LrMmQ5JHgPsmAByhQBg9BJUh2i8Vb',

  FARMS: {
    KUSD: {
      farm: 'KT1BWmQPzn8GcQkQTaU6tRFRgrpPQFpMYBtW',
      reserve: 'KT1EmweeRXWBQsRmzp3YrV4fftpS4nSdWPcx',
    },
    QLKUSD: {
      farm: 'KT1MQEKWeJC1ei95GwtJaezT4cQp8i5CNus8',
      reserve: 'KT1WmrPTHTFNzoC4BA34Hi9PS8qMJZAkFedQ',
    },
    KUSD_LP: {
      farm: 'KT1TgMN91K55if1caJgFQqM7BEazkpAxBFAJ',
      reserve: 'KT1JmgmXTDwsTxGpCYnNXuE8KKkR31JDdLbE',
    },
  },

  VESTING_CONTRACTS: {
    tz1YeYpdJshsXxkPdSdKUJaF1QmH1ngCrJ7V:
      'KT1DLXtc9NsmayRA6qUQqvmYZZFFU8UtRQMB',
    tz1Xh11mHYWxbYHv55AVhsPPPJeSp8PunERB:
      'KT1UEgx4By57wBjLz9GXQTMnnSyKdcYnpEQH',
    tz1cNABC2qtbbHKDDKdvxRkcyopL1kEfbpgV:
      'KT1WeBq1j8pg9Z9WwNNB1jVTySChUbNYkRND',
  },

  BREAK_GLASS_CONTRACTS: {
    // Break glass were never deployed to these on granada testnet
    MINTER: null,
    OVEN_PROXY: null,
    OVEN_FACTORY: null,
    TOKEN: null,
    OVEN_REGISTRY: null,
    DEVELOPER_FUND: null,
    STABILITY_FUND: null,
    ORACLE: null,
    LIQUIDITY_POOL: null,
    // These contracts are always deployed with break glass...
    DAO_COMMUNITY_FUND: 'KT1FzFgWsRewgNGP8nWvMykMiX7tekXbX1nS',
    VESTING_VAULTS: {
      tz1YeYpdJshsXxkPdSdKUJaF1QmH1ngCrJ7V:
        'KT1FgvFauNcxsoTFCd6ykjJWH5uPyjAnqgoS',
      tz1Xh11mHYWxbYHv55AVhsPPPJeSp8PunERB:
        'KT1XFsYrirqDRAkQe5wpEgGcNh1RX1RtXoiF',
      tz1cNABC2qtbbHKDDKdvxRkcyopL1kEfbpgV:
        'KT1U9nCXqWvJTN6qBChYZDZZh87RwkcurqkJ',
    },
  },
}

export default contracts
