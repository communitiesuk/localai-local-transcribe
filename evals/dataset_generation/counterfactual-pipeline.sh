#!/bin/bash
set -e

CONFIG="${1:-smoke_test.yaml}"

if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [CONFIG]"
    echo ""
    echo "Run the full counterfactual generation pipeline:"
    echo "  1. Generate synthetic transcript"
    echo "  2. Extract characteristics"
    echo "  3. Generate counterfactuals"
    echo ""
    echo "Arguments:"
    echo "  CONFIG    Config file name (default: smoke_test.yaml)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Uses smoke_test.yaml"
    echo "  $0 smoke_test.yaml    # Explicit smoke test"
    echo "  $0 full_dataset.yaml  # Full dataset generation"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Running full pipeline with config: $CONFIG"
echo ""

echo "1/3: Generating synthetic transcript..."
poetry run python -m evals.dataset_generation.transcription_generation.main --config "$CONFIG"

echo ""
echo "2/3: Extracting characteristics..."
poetry run python -m evals.dataset_generation.characteristics.src.main --config "$CONFIG"

echo ""
echo "3/3: Generating counterfactuals..."
poetry run python -m evals.dataset_generation.counterfactual_generation.src.main --config "$CONFIG"

echo ""
echo "✓ Pipeline complete with config: $CONFIG"
