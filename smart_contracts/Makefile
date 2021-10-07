SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./smartpy_out

# Run tests for the Minter contract
test-minter:
	$(SMART_PY_CLI) test minter.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Compile the minter
compile-minter:
	$(SMART_PY_CLI) compile minter.py MinterContract\(\) $(OUT_DIR)
	cp $(OUT_DIR)/minter_compiled.tz minter.tz
	rm -rf $(OUT_DIR)

# Run end to end tests
test-e2e:
	$(SMART_PY_CLI) test end-to-end-tests.py $(OUT_DIR)
	rm -rf $(OUT_DIR)
