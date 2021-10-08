SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./smartpy_out

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

# Compile the minter
compile-minter:
	$(SMART_PY_CLI) compile minter.py MinterContract\(\) $(OUT_DIR)
	cp $(OUT_DIR)/minter_compiled.tz minter.tz
	rm -rf $(OUT_DIR)

# Compile the Savings Pool
compile-savings-pool:
	$(SMART_PY_CLI) compile savings-pool.py SavingsPoolContract\(\) $(OUT_DIR)
	cp $(OUT_DIR)/savings-pool_compiled.tz savings-pool.tz
#	rm -rf $(OUT_DIR)

# Compile the Stability Fund
compile-stability-fund:
	$(SMART_PY_CLI) compile stability-fund.py StabilityFundContract\(\) $(OUT_DIR)
	cp $(OUT_DIR)/stability-fund_compiled.tz stability-fund.tz
#	rm -rf $(OUT_DIR)	

# Run end to end tests
test-e2e:
	$(SMART_PY_CLI) test end-to-end-tests.py $(OUT_DIR)
	rm -rf $(OUT_DIR)
