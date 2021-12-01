# Contracts 1.2

These contracts implement the a Minter that performs continuous interest accrual and implements onchain views. 
TODO(keefertaylor): Link the applicable KIPs here.

## Playbooks
### Sandboxnet

**Ensure up to date and clean checkout**
```
$ git pull
$ git status
```

**Ensure correct SmartPy Version**

TODO(keefertaylor): Audit this smartpy version and apply any fixes.
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

# TODOs
- generate real break glass storage
- static verification
- verify break glass
- gov proposal
- code to tabulate total loaned.
- post proposal verifications
- validate that we can init the contract
- fix any TODOs
- amountLoaned == amountMinted