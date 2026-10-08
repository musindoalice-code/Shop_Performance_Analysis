# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# COMMAND ----------

#create a sample data
months=["jan","Feb","March","April","May"]
Sale=[120,180,220,280,300]



# COMMAND ----------


import matplotlib.pyplot as plt
plt.plot(months, Sale)
plt.title("Monthly Sales")
plt.xlabel("Month")
plt.ylabel("Sales")
plt.show()

# COMMAND ----------

import matplotlib.pyplot as plt

x = [10, 20, 30, 40]
y = [20, 25, 35, 55]

plt.plot(x, y)
plt.title("Line Chart")
plt.ylabel('Y-Axis')
plt.xlabel('X-Axis')
plt.show()

# COMMAND ----------

import matplotlib.pyplot as plt

# Create a sample data
x=[1,2,3,4,5]
y=[2,4,3,5,7]

# 2 Create a line plot
plt.plot(x,y)

# Add labels and tittles
plt.title("My First Graph")
plt.xlabel("My X")
plt.ylabel("My Y")


# Display the graph
plt.show()

# COMMAND ----------

import matplotlib.pyplot as plt

# Step 1: Create sample data 
fruits=["Apples", "Bananas", "Cherries", "Kiwi"]
quantity =[10,15, 7, 12]

# Step 2: Create a bar chart
plt.bar(fruits,
        quantity)

# Step 3: Add labels
plt.title("Fruit Quantities")
plt.xlabel("Fruits")
plt.ylabel("Quantity")

# Step 4: Show the graph
plt.show()

# COMMAND ----------

 # Step 1: Create sample data 
fruits=["Apples", "Bananas", "Cherries", "Kiwi"]
quantity =[10,15, 7, 12]

# Step 2: Create a bar chart
plt.pie(quantity,
        labels=fruits)

# Create the pie chart
plt.title("Fruits Distribution")

# Show the pie chart
plt.show()

# COMMAND ----------

import matplotlib.pyplot as plt

x = ['Thur', 'Fri', 'Sat', 'Sun']
y = [170, 120, 250, 190]

plt.bar(x, y)
plt.title("Bar Chart")
plt.xlabel("Day")
plt.ylabel("Total Bill")
plt.show()

# COMMAND ----------

#This code plots a histogram to show frequency distribution of total bill values from the list x. It uses 10 bins and adds axis labels and a title for clarity

import matplotlib.pyplot as plt

x = [7, 8, 9, 10, 10, 12, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 18, 19, 20, 20,
     21, 22, 23, 24, 25, 25, 26, 28, 30, 32, 35, 36, 38, 40, 42, 44, 48, 50]

plt.hist(x, bins=10, color='steelblue')
plt.title("Histogram")
plt.xlabel("Total Bill")
plt.ylabel("Frequency")
plt.show()

# COMMAND ----------

#Pie chart is a circular chart used to show data as proportions or percentages. It is created using the pie(), where each slice (wedge) represents a part of the whole.
#Example: This code creates a simple pie chart to visualize distribution of different car brands. Each slice of pie represents the proportion of cars for each brand in the dataset.
import matplotlib.pyplot as plt

cars = ['AUDI', 'BMW', 'FORD','TESLA', 'JAGUAR',]
data = [23, 10, 35, 15, 12]

plt.pie(data, labels=cars, autopct='%1.1f%%')
plt.title(" Pie Chart")
plt.show()

# COMMAND ----------


#Box plot is a simple graph that shows how data is spread out. It displays the minimum, maximum, median and quartiles and also helps to spot outliers easily.
import matplotlib.pyplot as plt

data = [ [10, 12, 14, 15, 18, 20, 22],
         [8, 9, 11, 13, 17, 19, 21],
         [14, 16, 18, 20, 23, 25, 27] ]

plt.boxplot(data)
plt.xlabel("Groups")
plt.ylabel("Values")
plt.title("Box Plot")
plt.show()