# Kolibri.JS

<p align="center">
    <a href="https://discuss.kolibri.finance">
        <img src="https://img.shields.io/discourse/status?label=Forum&server=https%3A%2F%2Fdiscuss.kolibri.finance&style=for-the-badge" />
    </a>
    <a href="https://discord.gg/nkpSN467">
        <img src="https://img.shields.io/discord/790468417844412456?label=Discord&style=for-the-badge" />
    </a>
</p>
<p align="center">
    <a href="https://www.npmjs.com/package/@hover-labs/kolibri-js">
        <img src="https://img.shields.io/npm/v/@hover-labs/kolibri-js?style=for-the-badge" />
    </a>
</p>

Kolibri.JS contains code for interacting with the [Kolibri Protocol](https://kolibri.finance), a self balancing algorithmic stablecoin built on Tezos.

## Installation

As with other js packages, builds are pushed to [NPM](https://www.npmjs.com/package/@hover-labs/kolibri-js) and can be installed with

```
npm install --save @hover-labs/kolibri-js
```

## Documentation

Typedocs can be found at [this repo's github pages](https://hover-labs.github.io/kolibri-js/)

The following classes are implemented:
- `ContractErrors`: Maps errors from the Kolibri smart contracts into a user friendly enum
- `Network`: Enum defining available networks
- `HarbingerClient`: Interacts with the [Harbinger Oracle Contracts](https://github.com/tacoinfra/harbinger/)
- `LiquidityPoolClient`: Interacts with the [Kolibri Liquiidty Pool](https://kolibri.finance/liquidity-pool)
- `OvenClient`: Interacts with a Kolibri Oven
- `StableCoinClient`: Interacts with the top level Kolibri contracts
- `TokenClient`: Interacts with the FA1.2 kUSD token contract
- `CONTRACTS`: Helper object to get contract addresses on different networks
- `ConversionUtils`: Helpers to convert between units
- `ErrorUtils`: Error handling utilities
