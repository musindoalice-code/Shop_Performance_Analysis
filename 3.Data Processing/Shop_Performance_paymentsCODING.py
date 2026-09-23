# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports pandas and reads each CSV into its own table (called a DataFrame).
import pandas as pd
import numpy as np

df = spark.read.csv("shop_performance.shop_performance_data.shop_payments", header=True, inferSchema=True)

# Data Injestion
Payments=spark.table("shop_performance.shop_performance_data.shop_payments")
Payments=Payments.toPandas
display(Payments)

#shows rows and columns
print("Shape (rows, columns):", Payments.shape)

#shows each column's data type and whether it has missing values
Payments.info()

# previews the first 5 rows
Payments.head()

Payments.describe()

# .isnull().sum()- counts how many blank/missing cells are in each column, for each table.
print(Payments.isnull().sum())