# harbinger-lib

## About 

`harbinger-lib` is a self contained npm package written in typescript that contains functionality for working with the [Harbinger Price Oracle](https://github.com/tacoinfra/harbinger). To get started with Harbinger, visit the [main documentation](https://github.com/tacoinfra/harbinger).

This library provides base functionality for the [Harbinger CLI](https://github.com/tacoinfra/harbinger-cli), [Harbinger Poster](https://github.com/tacoinfra/harbinger-poster) and [Harbinger Signer](https://github.com/tacoinfra/harbinger-signer). This library is also useful for developers who want to interact with Harbinger functionality. Posters, signers, and users of Harbinger likely want to use one of the preceding higher level components.

## Functionality

`harbinger-lib` contains the following set of functionality:
- Programatically update an oracle contract from Coinbase or another provider
- Programatically deploy oracle or normalizer contracts
- Programatically push data from an oracle to a normalizer contract.
- Programatically perform account reveals if required
- Programatically revoke an oracle contract
- Retrieve pretty printed oracle data
- Utilities for working with bytes, common crypto functions (base58 encoding, hashing), encoding / decoding ASN1 payloads, and key manipulations
- Utilities for signing bytes from an [AWS KMS HSM](https://aws.amazon.com/kms/).

## Working with the Library

Before using functionality, clients will need to initialize the library with the following call:

```typescript
import { initOracleLib } from 'harbinger-lib'

initOracleLib()
```


## Building the Library

```shell
$ npm i
$ npm run build
```

## Credits

Harbinger is written and maintained by [Luke Youngblood](https://github.com/lyoungblood) and [Keefer Taylor](https://github.com/keefertaylor). 

