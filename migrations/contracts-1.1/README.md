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

```
sh <(curl -s https://smartpy.io/releases/20210708-4662b0f8b1fe2186a243078f9f1ba0a4aa1c6f16/cli/install.sh)
```

**Remove any stale data**
```
npm run install-submodules
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

Note: This action is destructive and the contract should not be used in production.

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

**Ensure correct SmartPy Version**

```
sh <(curl -s https://smartpy.io/releases/20210708-4662b0f8b1fe2186a243078f9f1ba0a4aa1c6f16/cli/install.sh)
```

**Remove any stale data**
```
npm run install-submodules
rm -f src/config.ts deploy-data.json
```

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
