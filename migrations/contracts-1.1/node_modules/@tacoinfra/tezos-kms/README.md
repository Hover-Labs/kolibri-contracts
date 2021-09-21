# Tezos KMS

## About 

`tezos-kms` is a typescript library which provides functionality for using keys stored in [AWS KMS](https://aws.amazon.com/kms/) for operations in [Tezos](https://tezos.com/). 

## Configuration

In order to use keys you will need to configure a key in AWS KMS. Steps 1-12 of the [Harbinger Setup Guide](https://github.com/tacoinfra/harbinger-signer#setup-instructions) provide a brief overview of how to achieve this.

## Usage

```js
import { TezosKmsClient } from '@tacoinfra/tezos-kms'

const awsKeyId = "x" // Place your key here.
const awsRegion = "eu-west-1"

const kmsClient = new TezosKmsClient(awsKeyId, awsRegion)

console.log(await kmsClient.getPublicKey()) // sppk...
console.log(await kmsClient.getPublicKeyHash()) // tz2...

const bytes = Buffer.from('deadbeef', 'hex')
console.log(await kmsClient.signOperation(bytes)) // <bytes>
console.log(await kmsClient.signOperationBase58(bytes)) // spsig...
```

## Building the Library

```shell
$ npm i
$ npm run build
```

## Credits

Harbinger is written and maintained by [Luke Youngblood](https://github.com/lyoungblood) and [Keefer Taylor](https://github.com/keefertaylor). 

