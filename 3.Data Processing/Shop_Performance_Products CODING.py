# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# import pandas as pd
# import numpy as np

# Data Injestion
Products = spark.table("shop_performance.shop_performance_data.shop_products")
Products_pd = Products.toPandas()
display(Products)

# COMMAND ----------

# DBTITLE 1,Checking the Data
# checking the data

# shows rows and columns
print("Shape (rows, columns):", Products_pd.shape)

# shows each column's data type and whether it has missing values
Products_pd.info()

# previews the first 5 rows
Products_pd.head()

# COMMAND ----------

# DBTITLE 1,Cleaning the Data
# cleaning the data

# .isnull().sum() -- counts how many blank or missing cells are in each column, for each table.
print(Products_pd.isnull().sum())

# .describe() shows min, max, average and other stats for numeric columns. 
print("--- Product prices ---")
print(Products_pd["UnitPrice"].describe())

# .duplicated().sum()- checks for duplicates
print(Products_pd.duplicated().sum())

# COMMAND ----------

# DBTITLE 1,Unique Values & Value Counts
# .unique()-show the distinct values in a column
Products_pd["ProductName"].unique()

# .value_counts() -show the distinct values in a column and number of times it appears
Products_pd["ProductName"].value_counts()

Products_pd["Category"].value_counts()

# COMMAND ----------

# DBTITLE 1,Orphan Products Check
# .isin()-finds orders whose ProductID doesn't exist in the products
orphan_Products  = Products_pd[~Products_pd["ProductID"].isin(Products_pd["ProductID"])]
print("ProductID with no matching product:", orphan_Products.shape[0])

# COMMAND ----------

# DBTITLE 1,Duplicate Products Check
#  Find all duplicate product IDs in the column
duplicate_ids = Products_pd['ProductID'][Products_pd['ProductID'].duplicated()]

# Filter the table to see all rows containing those duplicate IDs
duplicate_products = Products_pd[Products_pd['ProductID'].isin(duplicate_ids)]

print("Duplicate product entries found:", duplicate_products.shape[0])
print(duplicate_products)