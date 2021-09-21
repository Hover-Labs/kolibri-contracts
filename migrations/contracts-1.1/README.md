# Description

This script migrates contracts to the Contracts 1.1 branch (`keefertaylor/contracts-1.1`)

## Runbooks

### Testnet

**Ensure up to date and clean checkout**
```
$ git pull
$ git status
```

**Ensure correct SmartPy Version**



**Remove any stale data**
```
rm -f src/config.ts deploy-data.json
```

**Reset Sandbox**

Use the Discord bot!

**Run Migration**
```
export DEPLOY_SK=esdk...
cp src/config.sandbox.ts src/config.ts
ts-node src/flows/migrate.ts
```

**Validate Results**

Note: This action is destructive and the contract should not be used.

```
ts-node src/verifications/verify-storage.ts
ts-node src/verifications/verify-dao-and-break-glass.ts
```

**Generate Governance Lambda**
```
ts-node src/flows/generate-governance-lambda.ts
```

**Validation**

Validate the following in [the sandbox](https://sandbox.kolibri.finance/):
- A new oven can be created (tests that oven factory is wired correctly)
- New kUSD can be minted from the oven (tests that oven proxy and token are wired correctly)


### Mainnet

**Ensure up to date and clean checkout**
```
$ git pull
$ git status
```

**Remove any stale data**
```
rm -f src/config.ts deploy-data.json
```

**Reset Sandbox**
TODO

**Run Migration**
```
export DEPLOY_SK=esdk...
cp src/config.mainnet.ts src/config.ts
ts-node src/flows/migrate.ts
```

**Validate Results**

```
ts-node src/verifications/verify-storage.ts
```

**Generate Governance Lambda**
```
ts-node src/flows/generate-governance-lambda.ts
```
