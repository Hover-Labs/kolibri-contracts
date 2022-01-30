# Contracts 1.2.2

These contracts implement a Quipuswap Proxy

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

**Generate Governance Lambda**

```
ts-node src/flows/generate-governance-lambda.ts
```

**Post Governance Validation**

```
ts-node src/verifications/post-proposal-tests.ts
```

### Mainnet

Same as above, but use `config.mainnet.ts`
