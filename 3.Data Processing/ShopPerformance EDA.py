# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,import Libraries
#imports Library 
import pandas as pd
import numpy as np

# COMMAND ----------

# MAGIC %md
# MAGIC Data Ingestion

# COMMAND ----------

# DBTITLE 1,Customers
Customers=spark.table("shop_performance.shop_performance_data.shop_customers")
Customers=Customers.toPandas()
display(Customers)

# COMMAND ----------

# DBTITLE 1,orders table ingestion
#Loading table into pandas dataframe
Orders=spark.table("shop_performance.shop_performance_data.shop_orders")
Orders=Orders.toPandas()
display(Orders)

# COMMAND ----------

# DBTITLE 1,payment table injestion
Payments=spark.table("shop_performance.shop_performance_data.shop_payments")
Payments=Payments.toPandas()
display(Payments)

# COMMAND ----------

# MAGIC %md
# MAGIC Exploratory Data Analysis

# COMMAND ----------

# MAGIC %md
# MAGIC 1.Products EDA

# COMMAND ----------

 # checking the data

import pandas as pd
Products_pd = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()
# shows rows and columns
print("Shape (rows, columns):", Products_pd.shape)

# shows each column's data type and whether it has missing values
Products_pd.info()

# previews the first 5 rows
Products_pd.head()

# COMMAND ----------

# .unique shows the distinct values in a column
Products_pd["ProductName"].unique()

# COMMAND ----------

# shows the distinct values in a column and the number of times it appears
Products_pd["ProductName"].value_counts()

# COMMAND ----------

Products_pd["Category"].value_counts()

# COMMAND ----------

# shows each column's data type and whether it has missing values
Products_pd.info()

# COMMAND ----------

# .duplicated().sum()- checks for duplicates
print(Products_pd.duplicated().sum())

# COMMAND ----------

# .describe() shows min, max, average and other stats for numeric columns. 
Products_pd["UnitPrice"].describe()

# COMMAND ----------

print(Products_pd["UnitPrice"].min())
print(Products_pd["UnitPrice"].max())
print(Products_pd["UnitPrice"].mean())
print(Products_pd["UnitPrice"].count())

# COMMAND ----------

# MAGIC %md
# MAGIC 2.Orders EDA

# COMMAND ----------

#shows each column's data type and whether it has missing values
Orders.info()

# COMMAND ----------


# previews the first 5 rows
Orders.head()

# COMMAND ----------

Orders.shape

# COMMAND ----------

# .isnull().sum()- counts how many blank/missing cells are in each column 
print(Orders.isnull().sum())

# COMMAND ----------

# .duplicated().sum()- checks for duplicates
print(Orders.duplicated().sum())

# COMMAND ----------

Orders.drop_duplicates()

# COMMAND ----------

# MAGIC %md
# MAGIC 3.Payments EDA

# COMMAND ----------

 #shows rows and columns
Payments=spark.table("shop_performance.shop_performance_data.shop_payments")
Payments=Payments.toPandas()
print("Shape (rows, columns):", Payments.shape)

# COMMAND ----------

 #shows each column's data type and whether it has missing values
Payments.info()

# COMMAND ----------

# previews the first 5 rows
Payments.head()




# COMMAND ----------

Payments.describe()

# COMMAND ----------

 # .isnull().sum()- counts how many blank/missing cells are in each column, for each table.
print(Payments.isnull().sum())

# COMMAND ----------

#Count how many payments succeeded, failed, or are pending.
status_counts = Payments['PaymentStatus'].value_counts()
print(status_counts)

# COMMAND ----------

# MAGIC %md
# MAGIC 4.Customers EDA

# COMMAND ----------

# DBTITLE 1,Customers.shape()
Customers.shape
#shows rows and columns


# COMMAND ----------

Customers.info()
#shows each column's data type and whether it has missing values


# COMMAND ----------

Customers.head()
# previews the first 5 rows


# COMMAND ----------

Customers.columns



# COMMAND ----------

#checking the data type
#the age is a float which needs to be changed

Customers.dtypes

# COMMAND ----------

# DBTITLE 1,Convert Float to Integer
# Convert to integer while safely keeping missing values
Customers['Age'] = Customers['Age'].astype('Int64')
display(Customers[['Age']])

# COMMAND ----------

##cleaning the data-
#checking the null values
# .isnull().sum()- counts how many blank/missing cells are in each column, for each table. 
print(Customers.isnull().sum())

# COMMAND ----------

# MAGIC %md
# MAGIC #### we have Null Values on Age and City.Potentially we can replace or fill in the Null values with the mean age.We can replace the null values with unknown

# COMMAND ----------

# display the 119 rows where City is missing
null_city = Customers[Customers["City"].isnull()]
print(f"Number of missing City values: {len(null_city)}")
display(null_city)


# COMMAND ----------

# Replace null Age values with "Unknown"
# Age is currently a nullable integer (Int64), so we cast to object first
# to allow the string "Unknown" alongside numeric values.
Customers["Age"] = Customers["Age"].astype("object").fillna("Unknown")

print("Remaining nulls in Age:", Customers["Age"].isnull().sum())
display(Customers[["Age"]])

# COMMAND ----------

# DBTITLE 1,Unique
Customers["City"].unique()

# COMMAND ----------

# DBTITLE 1,City Value Counts
#Checking for inconsistent Spellings
city_counts = Customers["City"].value_counts()
print(city_counts)

# COMMAND ----------

# DBTITLE 1,Cleaning City Names
# .fillna-checking the city column-replaces the misspelled city names with the correct standard spelling, then fills any remaining blank City cells with "Unknown" so they're visible instead of silently missing.
Customers["City"] = Customers["City"].replace({
    "tehran": "Tehran",
    "Mashad": "Mashhad"})
Customers["City"] = Customers["City"].fillna("Unknown")

display(Customers["City"])

# COMMAND ----------

# DBTITLE 1,City Fix Verification
# .isnull- verifying the fix
print("\n--- City values after cleaning ---")
print(Customers["City"].value_counts())
print("\nRemaining nulls in City:", Customers["City"].isnull().sum())

# COMMAND ----------

Customers['SignupDate'] = pd.to_datetime(Customers['SignupDate'])
display(Customers)

# COMMAND ----------

#checking customer segment
distinct_value=Customers["CustomerSegment"].unique()
print(distinct_value)

# COMMAND ----------

# Shows each unique segment and how many times it appears
print(Customers["CustomerSegment"].value_counts())

# COMMAND ----------

# DBTITLE 1,VIP Analysis
VIP = Customers[Customers["CustomerSegment"] == "VIP"]
print(VIP)

# COMMAND ----------

Regular = Customers[Customers["CustomerSegment"] == "Regular"]
print(Regular)

# COMMAND ----------

New = Customers[Customers["CustomerSegment"] == "New"]
print(New)