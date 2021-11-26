SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./.smartpy_out

###### AGGREGATE TARGETS ###### 

all:
	make compile
	make test

compile:
	make compile-dev-fund
	make compile-minter
	make compile-oracle
	make compile-oven
	make compile-oven-factory
	make compile-oven-proxy
	make compile-oven-registry
	make compile-sandbox-oracle
	make compile-savings-pool
	make compile-stability-fund
	make compile-token

test:
	make test-dev-fund
	make test-minter
	make test-oracle
	make test-oven
	make test-oven-factory
	make test-oven-proxy
	make test-oven-registry
	make test-sandbox-oracle
	make test-savings-pool
	make test-stability-fund
	make test-token	
	make test-e2e

###### COMPILE AND TEST ###### 

dev-fund:
	make compile-dev-fund
	make test-dev-fund

minter:
	make compile-minter
	make test-minter

oracle:
	make compile-oracle
	make test-oracle

oven:
	make compile-oven
	make test-oven

oven-factory:
	make compile-oven-factory
	make test-oven-factory

oven-proxy:
	make compile-oven-proxy
	make test-oven-proxy

oven-registry:
	make compile-oven-registry
	make test-oven-registry

sandbox-oracle:
	make compile-sandbox-oracle
	make test-sandbox-oracle

savings-pool:
	make compile-savings-pool
	make test-savings-pool

stability-fund:
	make compile-stability-fund
	make test-stability-fund

token:
	make compile-token
	make test-token

###### TESTS ###### 

# Run tests for the Dev Fund contract
test-dev-fund:
	$(SMART_PY_CLI) test dev-fund.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Minter contract
test-minter:
	$(SMART_PY_CLI) test minter.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oracle contract
test-oracle:
	$(SMART_PY_CLI) test oracle.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven contract
test-oven:
	$(SMART_PY_CLI) test oven.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven Factory contract
test-oven-factory:
	$(SMART_PY_CLI) test oven-factory.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven Proxy contract
test-oven-proxy:
	$(SMART_PY_CLI) test oven-proxy.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven Registry contract
test-oven-regisry:
	$(SMART_PY_CLI) test oven-registry.py $(OUT_DIR)
	rm -rf $(OUT_DIR)	

# Run tests for the Sandbox Oracle contract
test-sandbox-oracle:
	$(SMART_PY_CLI) test sandbox-oracle.py $(OUT_DIR)
	rm -rf $(OUT_DIR)	

# Run tests for the Savings Pool contract
test-savings-pool:
	$(SMART_PY_CLI) test savings-pool.py $(OUT_DIR)
	rm -rf $(OUT_DIR)	

# Run tests for the Stability Fund contract
test-stability-fund:
	$(SMART_PY_CLI) test stability-fund.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Token contract
test-token:
	$(SMART_PY_CLI) test token.py $(OUT_DIR)
	rm -rf $(OUT_DIR)	

# Run end to end tests
test-e2e:
	$(SMART_PY_CLI) test end-to-end-tests.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

###### COMPILE TARGETs ######

# Compile the Dev Fund
compile-dev-fund:
	$(SMART_PY_CLI) compile dev-fund.py $(OUT_DIR)
	cp $(OUT_DIR)/dev-fund/step_000_cont_2_contract.tz dev-fund.tz
	rm -rf $(OUT_DIR)

# Compile the Minter
compile-minter:
	$(SMART_PY_CLI) compile minter.py $(OUT_DIR)
	cp $(OUT_DIR)/minter/step_000_cont_0_contract.tz minter.tz
	rm -rf $(OUT_DIR)

# Compile the Oracle
compile-oracle:
	$(SMART_PY_CLI) compile oracle.py $(OUT_DIR)
	cp $(OUT_DIR)/oracle/step_000_cont_0_contract.tz oracle.tz
	rm -rf $(OUT_DIR)

# Compile the Oven
compile-oven:
	$(SMART_PY_CLI) compile oven.py $(OUT_DIR)
	cp $(OUT_DIR)/oven/step_000_cont_0_contract.tz oven.tz
	rm -rf $(OUT_DIR)

# Compile the Oven Factory
compile-oven-factory:
	$(SMART_PY_CLI) compile oven-factory.py $(OUT_DIR)
	cp $(OUT_DIR)/oven-factory/step_000_cont_1_contract.tz oven-factory.tz
	rm -rf $(OUT_DIR)

# Compile the Oven Proxy
compile-oven-proxy:
	$(SMART_PY_CLI) compile oven-proxy.py $(OUT_DIR)
	cp $(OUT_DIR)/oven-proxy/step_000_cont_0_contract.tz oven-proxy.tz
	rm -rf $(OUT_DIR)

# Compile the Oven Registry
compile-oven-registry:
	$(SMART_PY_CLI) compile oven-registry.py $(OUT_DIR)
	cp $(OUT_DIR)/oven-registry/step_000_cont_0_contract.tz oven-registry.tz
	rm -rf $(OUT_DIR)	

# Compile the Sandbox Oracle
compile-sandbox-oracle:
	$(SMART_PY_CLI) compile sandbox-oracle.py $(OUT_DIR)
	cp $(OUT_DIR)/sandbox-oracle/step_000_cont_0_contract.tz sandbox-oracle.tz
	rm -rf $(OUT_DIR)	

# Compile the Savings Pool
compile-savings-pool:
	$(SMART_PY_CLI) compile savings-pool.py $(OUT_DIR)
	cp $(OUT_DIR)/savings-pool/step_000_cont_1_contract.tz savings-pool.tz
	rm -rf $(OUT_DIR)

# Compile the Stability Fund
compile-stability-fund:
	$(SMART_PY_CLI) compile stability-fund.py $(OUT_DIR)
	cp $(OUT_DIR)/stability-fund/step_000_cont_0_contract.tz stability-fund.tz
	rm -rf $(OUT_DIR)	

# Compile the Token
compile-token:
	$(SMART_PY_CLI) compile token.py $(OUT_DIR)
	cp $(OUT_DIR)/token/step_000_cont_0_contract.tz token.tz
	rm -rf $(OUT_DIR)	
