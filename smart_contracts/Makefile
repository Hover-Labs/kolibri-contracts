SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./.smartpy_out

###### AGGREGATE TARGETS ###### 

all:
	make test
	make compile

compile:
	make compile-oven
	make compile-minter
	make compile-savings-pool
	make compile-stability-fund

test:
	make test-minter
	make test-savings-pool
	make test-stability-fund
	make test-e2e

###### TESTS ###### 

# Run tests for the Minter contract
test-minter:
	$(SMART_PY_CLI) test minter.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Savings Pool contract
test-savings-pool:
	$(SMART_PY_CLI) test savings-pool.py $(OUT_DIR)
	rm -rf $(OUT_DIR)	

# Run tests for the Stability Fund contract
test-stability-fund:
	$(SMART_PY_CLI) test stability-fund.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run end to end tests
test-e2e:
	$(SMART_PY_CLI) test end-to-end-tests.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

###### COMPILE TARGETs ######

# Compile the Oven
compile-oven:
	$(SMART_PY_CLI) compile oven.py $(OUT_DIR)
	cp $(OUT_DIR)/oven/step_000_cont_0_contract.tz oven.tz
	rm -rf $(OUT_DIR)

# Compile the minter
compile-minter:
	$(SMART_PY_CLI) compile minter.py $(OUT_DIR)
	cp $(OUT_DIR)/minter/step_000_cont_0_contract.tz minter.tz
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
