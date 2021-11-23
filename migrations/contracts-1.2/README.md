# Contracts 1.2

These contracts implement the KSR. 

## Playbooks
### Sandboxnet

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
rm -rf src/config.ts deploy-data.json
```

**Reset Sandbox**

Use the Discord bot!

**Run Migration**

NOTE: The DEPLOY_SK account needs $3 of kUSD on it to complete this migration.

```
export DEPLOY_SK=esdk...
cp src/config.sandbox.ts src/config.ts
ts-node src/flows/migrate.ts
```

**Validate Results**

Validate storage:
```
ts-node src/verifications/verify-storage.ts
```

**Test Break Glass and DAO Integrations**

Note that these interactions will break glass and thus make the contracts inoperable. 

```
ts-node src/verifications/verify-pause-guardian-and-dao-and-break-glass.ts
```

**Generate Governance Lambda**

```
ts-node src/flows/generate-governance-lambda.ts
```

**Validation**

NOTE: The DEPLOY_SK account needs 10 XTZ on it to complete this migration.
NOTE: This validation will leave 10 XTZ in a newly deployed oven.

```
ts-node src/verifications/post-proposal-tests.ts
```

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
rm -rf src/config.ts deploy-data.json
```

**Run Migration**
```
export DEPLOY_SK=esdk...
cp src/config.mainnet.ts src/config.ts
ts-node src/flows/migrate.ts
```

**Validate Results**

Validate storage:
```
ts-node src/verifications/verify-storage.ts
```

**Generate Governance Lambda**

```
ts-node src/flows/generate-governance-lambda.ts
```

Submit to the DAO.

**Validation**

NOTE: The DEPLOY_SK account needs 10 XTZ on it to complete this migration.
NOTE: This validation will leave 10 XTZ in a newly deployed oven.

```
ts-node src/verifications/post-proposal-tests.ts
```
