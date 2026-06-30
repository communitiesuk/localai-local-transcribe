"""
Environmental Impact Assessment — full report runner.

Run individual modules to see a single section:
  poetry run python transcription.py
  poetry run python llm_inference.py
  poetry run python training.py
  poetry run python comparisons.py
  poetry run python aws.py

Run this file for the complete report:
  poetry run python calculations.py
"""

import aws
import comparisons
import llm_inference
import training
import transcription
import water


def main() -> None:
    transcription.display()
    llm_inference.display()
    training.display()
    water.display()
    comparisons.display()
    try:
        aws.display()
    except RuntimeError as e:
        print(f"\n[AWS report skipped: {e}]")


if __name__ == "__main__":
    main()
