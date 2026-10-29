import pandas as pd
customers = pd.read_csv("data/raw/customers.csv")
customers["city"] = customers['city'].str.strip().str.title()
print(customers['city'].value_counts())
gender_map = {"male" :"male","m":"male","female":"female","f":"female"}
customers['gender'] = customers['gender'].str.strip().str.lower().map(gender_map)
customers['gender'] = customers['gender'].fillna("unknown")
print(customers['gender'].value_counts())


