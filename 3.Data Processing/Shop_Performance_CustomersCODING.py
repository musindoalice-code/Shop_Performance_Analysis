# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports Library 
import pandas as pd
import numpy as np


# COMMAND ----------


# Data Injestion
Customers=spark.table("shop_performance.shop_performance_data.shop_customers")
Customers=Customers.toPandas()
display(Customers)

# COMMAND ----------

# DBTITLE 1,Checking the Data
##

# Customers.shape()

# Customers.info()

# Customers.head()

# Customers.columns()

# Customers.rows()


print("Shape (rows, columns):", Customers.shape)#shows rows and columns
Customers.info()#shows each column's data type and whether it has missing values
Customers.head()# previews the first 5 rows

# COMMAND ----------

#checking the data type
#the age is a float which needs to be changed
#
Customers.dtypes

# COMMAND ----------

# DBTITLE 1,Convert Float to Int
# Convert to integer while safely keeping missing values
Customers['Age'] = Customers['Age'].astype('Int64')
display(Customers[['Age']])

# COMMAND ----------

# DBTITLE 1,Cell 6
Customers['SignupDate'] = pd.to_datetime(Customers['SignupDate'])
display(Customers)

# COMMAND ----------

# DBTITLE 1,Cell 4
Customers["City"].unique()

# COMMAND ----------

# DBTITLE 1,Missing Values
##cleaning the data-
#checking the null values
# .isnull().sum()- counts how many blank/missing cells are in each column, for each table. 
print(Customers.isnull().sum())

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

# DBTITLE 1,Verifying City Fix
# .isnull- verifying the fix
print("\n--- City values after cleaning ---")
print(Customers["City"].value_counts())
print("\nRemaining nulls in City:", Customers["City"].isnull().sum())

# COMMAND ----------

# DBTITLE 1,Orphan Customers Check
# Load Orders to check for orphan customers
Orders = spark.table("shop_performance.shop_performance_data.shop_orders").toPandas()

# .isin-finds orders whose CustomerID doesn't exist in the customers
orphan_Customers = Orders[~Orders["CustomerID"].isin(Customers["CustomerID"])]
print("Orders with no matching customer:", orphan_Customers.shape[0])

# COMMAND ----------

#checking customer segment
distinct_value=Customers["CustomerSegment"].unique()
print(distinct_value)

# COMMAND ----------

# Shows each unique segment and how many times it appears
print(Customers["CustomerSegment"].value_counts())

# COMMAND ----------

# DBTITLE 1,Cell 13
# Calculate Amount from Orders (Quantity) × Products (UnitPrice)
Products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()
Orders_products = Orders.merge(Products[["ProductID", "UnitPrice"]], on="ProductID")
Orders_products["Amount"] = Orders_products["Quantity"] * Orders_products["UnitPrice"]

# Join with Customers to get CustomerSegment, then group and sum
customer_orders = Orders_products.merge(Customers[["CustomerID", "CustomerSegment"]], on="CustomerID")
segment_value = customer_orders.groupby("CustomerSegment")["Amount"].sum()
print(segment_value)

# COMMAND ----------

# DBTITLE 1,VIP Analysis
VIP = Customers[Customers["CustomerSegment"] == "VIP"]
print(VIP)