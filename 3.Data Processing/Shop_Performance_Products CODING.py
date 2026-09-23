# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports Library and reads each CSV into its own table (called a DataFrame).
import pandas as pd
import numpy as np

df = spark.read.csv("shop_performance.shop_performance_data.shop_products", header=True, inferSchema=True)

# Data Injestion
Products=spark.table("shop_performance.shop_performance_data.shop_products")
Products=Products.toPandas
display(Products)

##checking the data

#shows rows and columns
print("Shape (rows, columns):", Products.shape)

#shows each column's data type and whether it has missing values
Products.info()

# previews the first 5 rows
Products.head()

##cleaning the data

# .isnull().sum() -- counts how many blank or missing cells are in each column, for each table.
print(Products.isnull().sum())

# .describe() shows min, max, average and other stats for numeric columns. 
print("--- Product prices ---")
print(Products["UnitPrice"].describe())

# .duplicated().sum()- checks for duplicates
print(Products.duplicated().sum())

# .unique()-show the distinct values in a column
Products["ProductName"].unique()

# .value_counts() -show the distinct values in a column and number of times it appears
Products["ProductName"].value_counts()

Products["Category"].value_counts()

# .isin()-finds orders whose ProductID doesn't exist in the products
orphan_Products  = Products[~Products["ProductID"].isin(Products["ProductID"])]
print("ProductID with no matching product:", orphan_Products.shape[0])

#  Find all duplicate product IDs in the column
duplicate_ids = Products['ProductID'][Products['ProductID'].duplicated()]

# Filter the table to see all rows containing those duplicate IDs
duplicate_products = Products[Products['ProductID'].isin(duplicate_ids)]

print("Duplicate product entries found:", duplicate_products.shape[0])
print(duplicate_products)





#"products.csv — 
# no missing values,
#  no broken links, 
# prices sanity-checked (range $7–$260), 
# no cleaning needed."