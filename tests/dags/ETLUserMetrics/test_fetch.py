import sys, os
sys.path.insert(0, os.path.abspath("airflow/dags"))

from unittest.mock import patch
from ETLUserMetrics.pr_utils.fetch import fetch_batch


@patch("ETLUserMetrics.pr_utils.fetch.requests.get")
def test_fetch_batch_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": [{"email": "test@gmail.com"}]}

    result = fetch_batch("male", 0)
    assert isinstance(result, list)
    assert result[0]["email"] == "test@gmail.com"
