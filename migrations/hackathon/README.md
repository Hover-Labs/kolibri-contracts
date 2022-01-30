# Contracts 1.2.1

This migration nulls the quipu
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

**Choose a Config**
```
cp src/config.<CHOOSE ME>.ts src/config.ts
```

**Generate Governance Lambda**

```
ts-node src/flows/generate-governance-lambda.ts
```

Submit this proposal on the governance portal. 

**Post Governance Validation**

Validate the migration zero'ed the address and that deposits and withdrawals still work. 

NOTE: The DEPLOY_SK account needs 10 XTZ on it to complete this migration.
NOTE: This validation will leave 10 XTZ in a newly deployed oven.

```
ts-node src/verifications/post-proposal-tests.ts
```

