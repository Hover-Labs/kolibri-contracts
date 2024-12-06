#!/usr/bin/env bash

set -e -o pipefail

echo "----------------------------------------"
echo "Compiling StableCoin Contracts"
echo "----------------------------------------"

# Expected location of SmartPy CLI.
SMART_PY_CLI=~/smartpy-cli/SmartPy.sh

# Expected location of ligo.
LIGO_CLI=ligo

# Output directory
OUT_DIR=./.smartpy_out

# Parallel sorted arrays.
CONTRACTS_ARRAY=(oven-factory dev-fund token stability-fund minter oven-proxy oracle oracle-on-demand oven oven-registry sandbox-oracle savings-pool)

CONTRACTS_LIGO_ARRAY=("oracle-on-demand KolibriOracleAdapter")

# # Ensure we have a SmartPy binary.
if [ ! -f "$SMART_PY_CLI" ]; then
    echo "Fatal: Please install SmartPy CLI at $SMART_PY_CLI" && exit
fi

# Ensure we have a Ligo binary.
if [ ! -x "$(command -v $LIGO_CLI)" ]; then
    echo "Fatal: Please install Ligo CLI, https://ligolang.org/docs/intro/installation" && exit
fi

# Compile a contract.
# Args <contract name, ex: minter> <invocation, ex: MinterContract()> <out dir>
function processContract {
    CONTRACT_NAME=$1
    OUT_DIR=$2
    CONTRACT_IN="${CONTRACT_NAME}.py"
    CONTRACT_OUT="${CONTRACT_NAME}.tz"

    echo ">> Processing ${CONTRACT_NAME}"

    # Ensure file exists.
    if [ ! -f "$CONTRACT_IN" ]; then
        echo "Fatal: $CONTRACT_IN not found. Running from wrong dir?" && exit
    fi

    # Test
    echo ">>> [1 / 3] Testing ${CONTRACT_NAME} "
    $SMART_PY_CLI test $CONTRACT_IN $OUT_DIR
    echo ">>> Done"

    echo ">>> [2 / 3] Compiling ${CONTRACT_NAME}"
    $SMART_PY_CLI compile $CONTRACT_IN $INVOCATION $OUT_DIR
    echo ">>> Done."

    echo ">>> [3 / 3] Copying Artifacts"
    # Some contracts need to inherit or have other contracts, in which case they will be step_000_cont_1 or 2.
    # TODO(keefertaylor): This is pretty brittle. Consider if we should migrate to Makefile or find a better way.
    cp "$OUT_DIR/${CONTRACT_NAME}/step_000_cont_0_contract.tz" $CONTRACT_OUT || cp "$OUT_DIR/${CONTRACT_NAME}/step_000_cont_1_contract.tz" $CONTRACT_OUT || cp "$OUT_DIR/${CONTRACT_NAME}/step_000_cont_2_contract.tz" $CONTRACT_OUT 
    echo ">>> Written to ${CONTRACT_OUT}"

   
}

# Compile a ligo contract.
# Args <contract name, ex: oracle-on-demand> <module, ex: KolibriOracleAdapter>
function processContractLigo {
    CONTRACT_NAME=$1
    OUT_DIR=$2
    CONTRACT_IN="${CONTRACT_NAME}.jsligo"
    CONTRACT_OUT="${CONTRACT_NAME}.tz"

    echo ">> Processing ${CONTRACT_NAME}"

    # Ensure file exists.
    if [ ! -f "$CONTRACT_IN" ]; then
        echo "Fatal: $CONTRACT_IN not found. Running from wrong dir?" && exit
    fi

    # Test
    echo ">>> [1 / 3] Testing ${CONTRACT_NAME} "
    $LIGO_CLI run test $CONTRACT_IN
    echo ">>> Done"

    echo ">>> [2 / 3] Compiling ${CONTRACT_NAME}"
    $LIGO_CLI compile contract $CONTRACT_IN $INVOCATION -o $CONTRACT_OUT
    echo ">>> Done."
    echo ">>> Written to ${CONTRACT_OUT}"
}

echo "> [1 / 3] Unit Testing and Compiling Contracts."
rm -rf $OUT_DIR
for i in ${!CONTRACTS_ARRAY[@]}; do
    echo ">> [$((i + 1)) / ${#CONTRACTS_ARRAY[@]}] Processing ${CONTRACTS_ARRAY[$i]}"
    processContract ${CONTRACTS_ARRAY[$i]} ${INVOCATION_ARRAY[$i]} $OUT_DIR
    echo ">> Done."
    echo ""
done
for i in ${!CONTRACTS_LIGO_ARRAY[@]}; do
    set -- ${CONTRACTS_LIGO_ARRAY[$i]}
    echo ">> [$((i + 1)) / ${#CONTRACTS_LIGO_ARRAY[@]}] Processing $1"
    processContractLigo $1 $2
    echo ">> Done."
    echo ""
done
echo "> Compilation Complete."
echo ""

# End to End Testing
echo "> [2 / 3] Running End to End Tests"
$SMART_PY_CLI test end-to-end-tests.py $OUT_DIR
echo "> Testing Complete"
echo ""

# Remove other artifacts to reduce noise.
echo "> [3 / 3] Cleaning up"
rm -rf $OUT_DIR
echo "> All tidied up."
echo ""

echo "----------------------------------------"
echo "Task complete."
echo "----------------------------------------"