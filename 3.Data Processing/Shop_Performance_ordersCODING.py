# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports pandas and reads each CSV into its own table (called a DataFrame).
# import pandas as pd
# import numpy as np

df = spark.read.csv("shop_performance.shop_performance_data.shop_orders", header=True, inferSchema=True)

# Data Injestion
Orders=spark.table("shop_performance.shop_performance_data.shop_orders")
Orders=Orders.toPandas()
display(Orders)

#shows rows and columns
print("Shape (rows, columns):", Orders.shape)

#shows each column's data type and whether it has missing values
Orders.info()

# previews the first 5 rows
Orders.head()

##cleaning the data-

# .isnull().sum()- counts how many blank/missing cells are in each column 
print(Orders.isnull().sum())

# .duplicated()-Checking for Duplicate where it counts how many times each OrderID appears. 

duplicate_orders = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Number of duplicate OrderID rows:", duplicate_orders.shape[0])
duplicate_orders.sort_values("OrderID")

#inspect the duplicate OrderIDs-: shows the actual duplicate rows side by side, sorted by OrderID, so we see  different data under the same ID
dupes = Orders[Orders.duplicated(subset="OrderID", keep=False)].sort_values("OrderID")
dupes.head(20)

# .describe() Checking Numerical Values- shows min, max, average and other stats for numeric columns. .
print("\n--- Order quantity & discount ---")
print(Orders[["Quantity", "Discount"]].describe())


#Checking the negative quantity rows-filters to only the rows where Quantity is negative
negative_qty = Orders[Orders["Quantity"] < 0]
print("Count of negative quantity rows:", negative_qty.shape[0])
negative_qty

print("\n--- Duplicate OrderIDs ---")
dupes = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Count:", dupes.shape[0])

print("\n--- Orphan products (ProductID not in products.csv) ---")
orphan_products = Orders[~Orders["ProductID"].isin(Products["ProductID"])]
print("Count:", orphan_products.shape[0])

print("\n--- Quantity & Discount sanity check ---")
print(Orders[["Quantity", "Discount"]].describe())

print("\n--- Status values ---")
print(Orders["Status"].value_counts())

print("\n--- PaymentMethod values ---")
print(Orders["PaymentMethod"].value_counts())