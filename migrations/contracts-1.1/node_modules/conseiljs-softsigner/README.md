# ConseilJS-softsigner

[![npm version](https://img.shields.io/npm/v/conseiljs-softsigner.svg)](https://www.npmjs.com/package/conseiljs-softsigner)
[![npm](https://img.shields.io/npm/dm/conseiljs-softsigner.svg)](https://www.npmjs.com/package/conseiljs-softsigner)
[![Build Status](https://travis-ci.org/Cryptonomic/ConseilJS-softsigner.svg?branch=master)](https://travis-ci.org/Cryptonomic/ConseilJS-softsigner)
[![Coverage Status](https://coveralls.io/repos/github/Cryptonomic/ConseilJS-softsigner/badge.svg?branch=master)](https://coveralls.io/github/Cryptonomic/ConseilJS-softsigner?branch=master)
[![dependencies](https://david-dm.org/Cryptonomic/ConseilJS-softsigner/status.svg)](https://david-dm.org/Cryptonomic/ConseilJS-softsigner)

[ConseilJS](https://www.npmjs.com/package/conseiljs) software signer plugin for [ConseilJS-core](https://github.com/Cryptonomic/ConseilJS). Supports the ED25519 curve via libsodium for tz1-address operations on the Tezos platform.

## Use with Nodejs

Add our [NPM package](https://www.npmjs.com/package/conseiljs) to your project and a signing library.

```bash
npm i conseiljs
npm i conseiljs-softsigner
```

```javascript
import fetch from 'node-fetch';
import * as log from 'loglevel';

import { registerFetch, registerLogger, Signer, TezosMessageUtils } from 'conseiljs';
import { KeyStoreUtils, SoftSigner } from 'conseiljs-softsigner';

const logger = log.getLogger('conseiljs');
logger.setLevel('debug', false);
registerLogger(logger);
registerFetch(fetch);

let signer: Signer;
const keyStore = await KeyStoreUtils.restoreIdentityFromSecretKey('edskRgu8wHxjwayvnmpLDDijzD3VZDoAH7ZLqJWuG4zg7LbxmSWZWhtkSyM5Uby41rGfsBGk4iPKWHSDniFyCRv3j7YFCknyHH');
signer = new SoftSigner(TezosMessageUtils.writeKeyWithHint(keyStore.secretKey, 'edsk'));
```

## Use with React

TBD

## Use with React Native

TBD

## Use with Web

```html
<html>
<head>
    <script src="https://cdn.jsdelivr.net/gh/cryptonomic/conseiljs-softsigner/dist-web/conseiljs-softsigner.min.js"
        integrity="sha384-V1iaajn0x/SMFcZ9Y/xNQmqQSKyll6Dzt27U6OWiv8NdbHTVaHOGHdQ8g0G68HPd"
        crossorigin="anonymous"></script>
        <script>
            //conseiljssoftsigner.
        </script>
</head>
<body>
    ...
</body>
</html>
```
