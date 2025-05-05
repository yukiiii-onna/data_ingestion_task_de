import requests
import pandas as pd

response = requests.get("https://fakerapi.it/api/v2/persons?_quantity=100&_gender=male")
data = response.json()["data"]
df = pd.DataFrame(data)
df.to_csv("/app/scripts/sample_api.csv", index=False)
