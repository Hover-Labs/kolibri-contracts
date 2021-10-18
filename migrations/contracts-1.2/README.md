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
ts-node src/verifications/verify-dao-and-break-glass.ts
```

**Generate Governance Lambda**

TODO(keefertaylor): Write this.

Need to:
- set stability fund on minter
- transfer stability fund value
- validate that stability fund is not referenced elsewhere

**Validation**

TODO(keefertaylor): Come up with validation logic - this could be automatable.

Need to: 
- validate fund received previous value
- validate that future interest accrues to correct stability fund.
- validate that interest can be paid

### Mainnet
TODO
  // Governance: 
  // - Set stability fund
  // - transfer stability fund

