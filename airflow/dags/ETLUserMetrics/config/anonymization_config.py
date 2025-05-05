
ANONYMIZATION_CONFIG = {
    "firstname":lambda x: "****",
    "lastname":lambda x: "****",
    "email": lambda x: f"****@{x.split('@')[1]}" if isinstance(x, str) and "@" in x else "unknown",
    "phone": lambda x: "****",
    "street": lambda x: "****",
    "streetName": lambda x: "****",
    "buildingNumber": lambda x: "****",
    "zipcode": lambda x: "****",
    "latitude": lambda x: "****",
    "longitude": lambda x: "****",
}

NESTED_FIELDS = ["address"]