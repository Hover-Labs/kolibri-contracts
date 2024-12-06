SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./.smartpy_out

LIGO_CLI := ligo

# Ensure we have a Ligo binary.
check-ligo:
	@type $(LIGO_CLI) >/dev/null 2>&1

###### AGGREGATE TARGETS ###### 

all:
	make test
	make compile

# TODO(keefertaylor): Write rules for all contracts, and add them here.
compile:
	make compile-dev-fund
	make compile-minter
	make compile-oven
	make compile-oven-proxy
	make compile-savings-pool
	make compile-stability-fund
	make compile-token
	make compile-oracle-on-demand

# TODO(keefertaylor): Write rules for all contracts, and add them here.
test:
	make test-dev-fund
	make test-minter
	make test-oven
	make test-oven-proxy
	make test-savings-pool
	make test-stability-fund
	make test-token	
	make test-e2e
	make test-oracle-on-demand

###### TESTS ###### 

# Run tests for the Dev Fund contract
test-dev-fund:
	$(SMART_PY_CLI) test dev-fund.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Minter contract
test-minter:
	$(SMART_PY_CLI) test minter.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven contract
test-oven:
	$(SMART_PY_CLI) test oven.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oven Proxy contract
test-oven-proxy:
	$(SMART_PY_CLI) test oven-proxy.py $(OUT_DIR)
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

# Compile the Oven
compile-oven:
	$(SMART_PY_CLI) compile oven.py $(OUT_DIR)
	cp $(OUT_DIR)/oven/step_000_cont_0_contract.tz oven.tz
	rm -rf $(OUT_DIR)

# Compile the Oven Proxy
compile-oven-proxy:
	$(SMART_PY_CLI) compile oven-proxy.py $(OUT_DIR)
	cp $(OUT_DIR)/oven-proxy/step_000_cont_0_contract.tz oven-proxy.tz
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

compile-oracle-on-demand: check-ligo
	$(LIGO_CLI) compile contract oracle-on-demand.jsligo -m KolibriOracleAdapter -o oracle-on-demand.tz

test-oracle-on-demand: check-ligo
	$(LIGO_CLI) run test oracle-on-demand.jsligo