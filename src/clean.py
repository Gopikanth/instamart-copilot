import pandas as pd
customers = pd.read_csv("data/raw/customers.csv")
customers["city"] = customers['city'].str.strip().str.title()
print(customers['city'].value_counts())
gender_map = {"male" :"male","m":"male","female":"female","f":"female"}
customers['gender'] = customers['gender'].str.strip().str.lower().map(gender_map)
customers['gender'] = customers['gender'].fillna("unknown")
print(customers['gender'].value_counts())
customers.loc[(customers["age"] < 10) | (customers["age"] > 100), "age"] = float("nan")
print(customers["age"].isna().sum())
customers.groupby('city')['age'].mean()
city_median = (customers.groupby('city')['age'].transform('median'))
print(city_median.head())
customers['age'] =customers['age'].fillna(city_median)
print(customers['age'].isna().sum())
print(customers["age"].min(), customers["age"].max())
customers['signup_date'] = pd.to_datetime(customers['signup_date'])
print(customers.dtypes)
print(customers["city"].value_counts())
print(customers["gender"].value_counts())
print(customers["age"].isna().sum(), customers["age"].min(), customers["age"].max())


