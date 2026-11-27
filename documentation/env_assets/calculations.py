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

import argparse

import aws
import comparisons
import llm_inference
import training
import transcription
import water


def main(*, api_calls: bool = False) -> None:
    aws_data = aws.calculate(api_calls=api_calls)
    transcription.display()
    llm_inference.display()
    training.display()
    water.display(aws_data)
    comparisons.display()
    aws.display(aws_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api_calls",
        action="store_true",
        help="Use AWS API calls for development/staging only. DO NOT use for production.",
    )
    args = parser.parse_args()
    main(api_calls=args.api_calls)
