# Conseil KMS

## About 

`kms-conseil` is a library which provides [ConseilJS](https://github.com/cryptonomic/conseiljs) `Signer` and `KeyStore` interfaces for working with keys stored in [AWS KMS](https://aws.amazon.com/kms/). This library acts as a binding between ConseilJS and AWS KMS for working with operations in [Tezos](https://tezos.com/). 

For more information on ConseilJS, see the [ConseilJS Documentation](https://cryptonomic.github.io/ConseilJS/#/).

## Configuration

In order to use keys you will need to configure a key in AWS KMS. Steps 1-12 of the [Harbinger Setup Guide](https://github.com/tacoinfra/harbinger-signer#setup-instructions) provide a brief overview of how to achieve this.

## Usage

```js
import { KmsKeyStore, KmsKeyStore } from '@tacoinfra/conseil-kms'
import { TezosNodeWriter } from 'conseiljs';

const awsKeyId = "x" // Place your key here.
const awsRegion = "eu-west-1"

const signer = new KmsSigner(awsKeyId, awsRegion)
const keystore = KmsKeyStore.from(awsKeyId, awsRegion)

const result = await TezosNodeWriter.sendTransactionOperation(
    "https://rpctest.tzbeta.net", 
    signer, 
    keystore, 
    'tz1RVcUP9nUurgEJMDou8eW3bVDs6qmP5Lnc',     // Recipient
    500_000,                                    // Amount, in mutez
    1500                                        // Fee, in mutez
)

```

## Building the Library

```shell
$ npm i
$ npm run build
```

## Credits

This library is written and maintained by [Luke Youngblood](https://github.com/lyoungblood) and [Keefer Taylor](https://github.com/keefertaylor). 

