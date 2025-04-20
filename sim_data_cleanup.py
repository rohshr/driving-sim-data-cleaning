import operator
import pandas as pd

# def load_csv(file_path):
#     """
#     Load the contents of a CSV file into a pandas DataFrame with numeric data types.

#     Args:
#         file_path (str): Path to the CSV file.

#     Returns:
#         DataFrame: A pandas DataFrame containing the CSV data with numeric values.
#     """
#     try:
#         data = pd.read_csv(file_path, header=0)  # Treat the first row as column headers
#         data = data.apply(pd.to_numeric, errors='coerce')  # Convert all data to numeric, coercing errors to NaN
#         return data
#     except FileNotFoundError:
#         print(f"Error: File not found at {file_path}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return pd.DataFrame()

def split_csv_by_headers(file_path, headers):
    """
    Splits a CSV file into multiple DataFrames based on rows where the headers appear as values.
    Ensures that the extracted values in the DataFrames are numeric.

    Args:
        file_path (str): Path to the CSV file.
        headers (list): List of header names to identify split points.

    Returns:
        list: A list of DataFrames, each corresponding to a section of the CSV file.
    """
    try:
        # Load the CSV file into a DataFrame
        data = pd.read_csv(file_path, header=None)  # No header row initially

        # Normalize headers and data for comparison
        normalized_headers = [header.strip().lower() for header in headers]
        normalized_data = data.apply(lambda row: row.map(lambda x: x.strip().lower() if isinstance(x, str) else x), axis=1)

        # Find the indices of rows where the headers appear
        header_indices = normalized_data[normalized_data.apply(
            lambda row: list(row) == normalized_headers, axis=1
        )].index.tolist()

        # Debugging: Print header indices
        print("Header Indices:", header_indices)

        # Split the data into separate DataFrames
        dataframes = []
        for i in range(len(header_indices)):
            start_idx = header_indices[i]
            end_idx = header_indices[i + 1] if i + 1 < len(header_indices) else len(data)

            # Extract the section and assign proper headers
            section = data.iloc[start_idx + 1:end_idx]
            section.columns = data.iloc[start_idx].values

            # Convert all values to numeric, coercing errors to NaN
            section = section.apply(pd.to_numeric, errors='coerce')

            dataframes.append(section)

        return dataframes

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to find a row based on a condition
def find_row(data, direction, column_name, threshold, comparison):
    """
    Find the first row in the data where the specified column is coompared with threshold.

    Args:
        data (list): List of dictionaries containing participant data.
        direction (str): Direction to read the rows.
        column_name (str): Name of the column to check.
        threshold (float): Threshold value.
        comparison (str): Comparison operator ('lt', 'le', 'eq', 'ne', 'gt', 'ge').

    Returns:
        int: Index of the first row where the condition is met, or -1 if not found.
    """
    operations = {
        "lt": operator.lt,   # less than
        "le": operator.le,   # less than or equal to
        "eq": operator.eq,   # equal to
        "ne": operator.ne,   # not equal to
        "gt": operator.gt,   # greater than
        "ge": operator.ge    # greater than or equal to
    }
    
    if comparison not in operations:
        raise ValueError(f"Unsupported comparison: {comparison}")
    
    if direction == 'down':
        for index, row in data.iterrows():
            if row['time'] != 0 and operations[comparison](row[column_name], threshold):
                return index
    elif direction == 'up':
        for index, row in reversed(data.iterrows()):
            if row['time'] != 0 and operations[comparison](row[column_name], threshold):
                return index
    return -1

# Example usage
file_path = 'participant3.csv'
headers = ['time', 'throttle', 'brake', 'steering', 'speed', 'ttc']
dataframes = split_csv_by_headers(file_path, headers)

print(f"Total DataFrames created: {len(dataframes)}")



# Go through each of the 27 dataframes
for i, df in enumerate(dataframes):
    # Add a column to df called speed_change that is the difference between the current speed and the speed 30 rows above; roughly after a second time
    df['speed_change'] = df['speed'].diff(30).fillna(0)  # Fill NaN with 0 for the first 30 rows
    # print(f"DataFrame {i + 1}:")
    # print(df.head(10))
    # print(f"Original Index Range: {df.index.min()} to {df.index.max()}")

    # Finding the upper_bound and lower_bound pairs for 27 crashes: Main task

    first_index = 0 
    last_index = 0
    # previous_last_index = 0 # Variable to store the lower bound of the previous crash
    upper_bound = 0
    lower_bound = 0

    """
    Find out the upper and lower bounds for the 27 crashes in the data set.
    ## Input: dataset
    ## Output : upper bound and lower bound values
    """
    
    # Finding first row where the speed is less than 15.99 (step 2)
    def is_speed_decreasing(current_speed, next_speed):
        """
        if current_speed < 15.99 and row['speed'] > row['speed'].shift(-1):
        
        Args:
            current_speed (float): Current speed value.
            next_speed (float): Speed value in the next row.
        
        Returns:
            bool: True if the speed is below 15.99 and decreasing, False otherwise.
        """
        return current_speed < 15.99 and next_speed < current_speed

    for index, row in df.iloc[0:].iterrows():
        # Extract the current speed value from the 'speed' column for the current row
        current_speed = row['speed']
        if index + 1 in df.index:  # Ensure the next index exists
            next_speed = df.loc[index + 1, 'speed'] # speed value in the next row
            if is_speed_decreasing(current_speed, next_speed):
                first_index = index   
                break
    
    # If somehow the participant didn’t slow down below 15.99, instead, find the first row where the |steering input| >= 7.0
    if first_index == 0: 
        for index, row in df.iloc[0:].iterrows():
            if abs(row['steering']) >= 7.0 and (row['time'] > 2): # checks for steering input greater than 7.0 after 2 seconds
                first_index = index
                break

    # print(first_index)
    
    """
    identify End of Event (Post-Takeover):

        Either speed ≤ 0.9 OR speed increases by ≥ 1.00 over a 10-row period
    """
    # print("First Index:", first_index)
    # print(df.loc[first_index:])


    # 1st row, where the speed starts to increase by 1 over the period of 10 rows or if it reaches 0.9 or less
    # last_index = find_row(df.loc[first_index:], 'down', 'speed_change', 1.0, 'ge') or find_row(df.loc[first_index:], 'down', 'speed', 0.9, 'le')

    # lower_bound = last_index
    if first_index not in df.index:
        print(f"Error: first_index {first_index} is out of bounds for the DataFrame. Skipping this DataFrame.")
        continue

    for index, row in df.loc[first_index:].iterrows():
        if row['speed'] <= 0.9:
            last_index = index - 1  # Subtract 1 to reference the last valid row before the condition fails
            break
    if last_index == 0: # If the last index is still 0, it means we didn't find a speed <= 0.9
        for index, row in df.loc[first_index:].iterrows():
            # if row['speed_change'] >= 1.0:
            # current_speed = row['speed']
            # previous_speed = df.loc[index - 50, 'speed'] if index - 50 in df.index else 0 # 50 rows before the current index; approximately 1 second
            
            # for x, y in df.loc[:first_index].iterrows():
            #     if row['time'] - y['time'] >= 2.0:
            #         previous_speed = y['speed']
            #         break
            acceleration = round((row['speed'] - df.loc[index - 50, 'speed']) / (row['time'] - df.loc[index - 50, 'time']), 6) if index - 50 in df.index else 0  # 50 rows before the current index; approximately 1 second
            ## to fix
            if acceleration >= 1.0:
                last_index = index
                # print(f"Acceleration: {acceleration}, Index: {index}")
                break
            else:
                last_index = df.index[-1] # If no valid last index is found, set it to the last index of the DataFrame
                # print(f"Acceleration: {acceleration}, Index: {index}")
                break
    lower_bound = last_index
    # print(f"First Index: {first_index}, Last Index: {last_index}")
    
    # """
    # Finding the upper bound
    # Finding first row where the TTC value was 1.95 or less. 
    # """

    # # This creates a new DataFrame with the rows from the first row of the sub data frame to the first_index in reverse order
    # # For going up the rows from the start point we found in step 2
    temp_df = df.loc[:first_index].iloc[::-1]

    start = False # Variable to track if we are in the range of interest
    upper_bound_found = False # Variable to track if we have found the upper bound

    while not upper_bound_found:
        for index, row in temp_df.iterrows():
            # print(index, index - 1)
            if row['ttc'] > 0 and row['ttc'] <= 1.95:
                start = True
                
            if start and (row['ttc'] == 0 or row['ttc'] > 1.95):
                if (temp_df.loc[index + 1, 'ttc'] - row['ttc']) > 0 and index + 1 in temp_df.index:
                    # print(temp_df.loc[index + 1, 'ttc'] - row['ttc'])
                    # print(index)
                    upper_bound = index + 1
                    # print("first row where ttc value was 1.95 or less")
                    # print(upper_bound)
                    start = False
                    upper_bound_found = True
                    break
        if not upper_bound_found: # If the loop ends without finding a valid upper bound
            for index, row in temp_df.iterrows():
                if row['brake'] > 0:
                    start = True
                    
                elif start and row['brake'] == 0:
                    brake_start = index + 2
                    upper_bound = brake_start
                    # print("first row where brake was initiated")
                    # print(brake_start)
                    start = False
                    upper_bound_found = True
                    break
                
                elif not(start) and row['brake'] == 0:
                    if abs(row['steering']) >= 7.00:
                        start = True
                        
                    elif start and abs(row['steering']) < 7.00:
                        steering_start = index + 1
                        upper_bound = steering_start
                        # print("first row where steering was initiated")
                        # print(steering_start)
                        start = False
                        upper_bound_found = True
                        break
        
        break # Break the while loop if upper bound is not found
            # if row['speed'] > 17.0:
            #     print("first row where speed decresead to below 17.0")
            #     print(index)

    # print("Upper Bound:", upper_bound - 5, "Lower Bound:", lower_bound)
    print(upper_bound - 5, lower_bound)
    # upper_bound_found = False
    # upper_bound = find_row(temp_df, 'up', 'ttc', 1.95, 'le') # 1st row, where the TTC variable reaches is greater than 0 and less than 1.95
    # if upper_bound == -1: # If somehow the participant didn’t slow down below 1.95, instead, find the first row where ...
    #     upper_bound = find_row(temp_df, 'up', 'brake',)

    ## look up to find the upper bound

    # def calculate_RT(data, upper_bound, lower_bound):
    #     """
    #     Calculate the reaction time (RT) for each row in the data.

    #     Args:
    #         data (list): List of dictionaries containing participant data.
    #         upper_bound (int): Upper bound for RT calculation.
    #         lower_bound (int): Lower bound for RT calculation.

    #     Returns:
    #         list: A list of dictionaries with calculated RT values.
    #     """
    #     # get the data from the csv dataframe which consists of the rows starting from the upper_bound to lower_bound
    #     data_range = data[upper_bound:lower_bound]
    #     print_table(data_range)
    #     # print(data_range)
    """
        =INDEX(
            INDIRECT("A"&lower_bound&":A"&upper_bound), # data 
            MATCH(1, 
                (
                    (INDIRECT("F"&lower_bound&":F"&upper_bound) <= 1.95) *
                    (INDIRECT("F"&lower_bound&":F"&upper_bound) > 0)), 
                0)
            ) -
        INDEX(
            INDIRECT("A"&lower_bound&":A"&upper_bound), 
            MATCH(1, 
                (
                    (INDIRECT("C"&lower_bound&":C"&upper_bound) >= 0.4) +
                    (ABS(INDIRECT("D"&lower_bound&":D"&upper_bound)) >= 10)) * 
                1, 
            0))

        A = time
        B = throttle
        C = brake
        D = steering
        E = speed
        F = TTC
    """