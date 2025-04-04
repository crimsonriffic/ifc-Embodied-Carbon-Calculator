import pandas as pd
import pytest
import os
import sys

from calculator_processor.utils.calculator import (
    calculate_embodied_carbon,
    calculate_gfa,
)
from calculator_processor.utils import utils


def load_ec_test_cases():
    return pd.read_csv("tests/data/test_ec.csv")


def load_gfa_test_cases():
    return pd.read_csv("tests/data/test_gfa.csv")


def normalize_s3_path(path):
    """Normalize S3 path by removing 's3://' prefix if present"""
    return path.replace("s3://", "") if isinstance(path, str) else path


@pytest.mark.parametrize("test_case", load_ec_test_cases().to_dict("records"))
def test_ec_calculations(s3_client, test_case):
    normalized_path = normalize_s3_path(test_case["ifc_path"])

    try:
        ifc_bytes = utils.get_ifc_by_filepath(
            s3_client=s3_client, s3_bucket="ifcfiles", s3_file_path=normalized_path
        )

        if ifc_bytes is None:
            pytest.fail(f"Failed to fetch IFC file from S3: {test_case['ifc_path']}")

        tolerance = 0.01
        with utils.temp_ifc_file(ifc_bytes) as tmp_path:
            result = calculate_embodied_carbon(tmp_path)
            expected = test_case["expected_ec"]

        assert abs(result - expected) <= tolerance * expected, (
            f"EC calculation for {test_case['name']} failed. "
            f"Expected {expected} ± {tolerance}%, got {result}"
        )

    except Exception as e:
        pytest.fail(f"Test failed for {test_case['ifc_path']}: {str(e)}")


@pytest.mark.parametrize("test_case", load_gfa_test_cases().to_dict("records"))
def test_gfa_calculations(s3_client, test_case):
    normalized_path = normalize_s3_path(test_case["ifc_path"])

    try:
        ifc_bytes = utils.get_ifc_by_filepath(
            s3_client=s3_client, s3_bucket="ifcfiles", s3_file_path=normalized_path
        )

        if ifc_bytes is None:
            pytest.fail(f"Failed to fetch IFC file from S3: {test_case['ifc_path']}")
        tolerance = 0.01
        with utils.temp_ifc_file(ifc_bytes) as tmp_path:
            result = calculate_gfa(tmp_path)
            expected = test_case["expected_gfa"]

        assert abs(result - expected) <= tolerance * expected, (
            f"EC calculation for {test_case['name']} failed. "
            f"Expected {expected} ± {tolerance}%, got {result}"
        )

    except Exception as e:
        pytest.fail(f"Test failed for {test_case['ifc_path']}: {str(e)}")
