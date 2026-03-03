#!/bin/bash
# Run the E2E test and save output to output/test_output.txt
# Usage: bash run_test.sh [headed]
#   bash run_test.sh          → headless
#   bash run_test.sh headed   → visible browser with slow_mo

cd "$(dirname "$0")"
mkdir -p output

if [ "$1" = "headed" ]; then
    export HEADLESS=false
    export SLOW_MO=500
fi

.venv/bin/pytest tests/test_e2e_workflow.py -v -s --tb=long 2>&1 | tee output/test_output.txt

echo ""
echo "Output saved to: output/test_output.txt"
echo "Screenshots in:  output/"
