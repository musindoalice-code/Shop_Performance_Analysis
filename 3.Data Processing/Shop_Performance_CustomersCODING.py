# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports Library and reads each CSV into its own table (called a DataFrame).
import pandas as pd
import numpy as np

df = spark.read.csv("shop_performance.shop_performance_data.shop_customers", header=True, inferSchema=True)

# Data Injestion
Customers=spark.table("shop_performance.shop_performance_data.shop_customers")
Customers=Customers.toPandas
display(Customers)

##checking the data

# Customers.shape()

# Customers.info()

# Customers.head()

# Customers.columns()

# Customers.rows()


print("Shape (rows, columns):", Customers.shape)#shows rows and columns
Customers.info()#shows each column's data type and whether it has missing values
Customers.head()# previews the first 5 rows

##cleaning the data-

# .isnull().sum()- counts how many blank/missing cells are in each column, for each table. 
print(Customers.isnull().sum())

#Checking for inconsistent Spellings
city_counts = Customers["City"].value_counts()
print(city_counts)

# .fillna-checking the city column-replaces the misspelled city names with the correct standard spelling, then fills any remaining blank City cells with "Unknown" so they're visible instead of silently missing.
Customers["City"] = Customers["City"].replace({
    "tehran": "Tehran",
    "Mashad": "Mashhad"})
Customers["City"] = Customers["City"].fillna("Unknown")

# .isnull- verifying the fix
print("\n--- City values after cleaning ---")
print(Customers["City"].value_counts())
print("\nRemaining nulls in City:", Customers["City"].isnull().sum())

# .isin-finds orders whose CustomerID doesn't exist in the customers
orphan_Customers = Orders[~Orders["CustomerID"].isin(Customers["CustomerID"])]
print("Orders with no matching customer:", orphan_Customers.shape[0])