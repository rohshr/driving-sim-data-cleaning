import operator
import pandas as pd

data = pd.read_csv("participant3.csv", header=0)

# print(data)

print(data.iloc[1:7])  # Access rows from row 2 to row 7 (index 1 to 6)

# #loop through the first 5 rows
# for index, row in data.iloc[3:10].iterrows():
#     print(f"Speed {row['speed']}        Speed +1 {data.iloc[index + 1]['speed']}")
#     # print("Speed + 1", data.iloc[index + 1]['speed'])  
