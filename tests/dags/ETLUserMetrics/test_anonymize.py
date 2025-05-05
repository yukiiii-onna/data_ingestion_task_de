import sys, os
sys.path.insert(0, os.path.abspath("airflow/dags"))

from ETLUserMetrics.pr_utils.anonymize import anonymize_users


def test_anonymize_users_basic_fields():
    input_data = [
        {
            "firstname": "Alice",
            "lastname": "Smith",
            "email": "alice@example.com",
            "phone": "+1234567890",
            "address": {
                "street": "123 Main St",
                "zipcode": "12345",
                "latitude": "50.0",
                "longitude": "8.0"
            }
        }
    ]

    df = anonymize_users(input_data)

    assert df.iloc[0]["firstname"] == "****"
    assert df.iloc[0]["lastname"] == "****"
    assert df.iloc[0]["email"] == "****@example.com"
    assert df.iloc[0]["phone"] == "****"
    assert df.iloc[0]["street"] == "****"
    assert df.iloc[0]["zipcode"] == "****"
    assert df.iloc[0]["latitude"] == "****"
    assert df.iloc[0]["longitude"] == "****"


def test_anonymize_users_handles_missing_fields():
    input_data = [
        {
            "email": "noaddress@gmail.com",  # no address block at all
        }
    ]

    df = anonymize_users(input_data)

    assert df.iloc[0]["email"] == "****@gmail.com"
    assert "street" not in df.columns  # since address was missing
