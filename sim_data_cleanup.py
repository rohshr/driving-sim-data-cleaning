import operator
import pandas as pd

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

def is_speed_decreasing(current_speed, next_speed, speed_threshold=15.99):
    """
    if current_speed < 15.99 and row['speed'] > row['speed'].shift(-1):
    
    Args:
        current_speed (float): Current speed value.
        next_speed (float): Speed value in the next row.
    
    Returns:
        bool: True if the speed is below 15.99 and decreasing, False otherwise.
    """
    return current_speed < speed_threshold and next_speed < current_speed

# function to find the upper bound based on TTC values
def find_upper_bound_ttc(temp_df, speed_threshold=None):
    start = False
    upper_bound_found = False
    upper_bound = None  # Default value if no upper bound is found

    for index, row in temp_df.iterrows():
        if row['ttc'] > 0 and row['ttc'] <= 1.95:
            start = True
                
        elif start and (speed_threshold is None or row['speed'] < speed_threshold) and (row['ttc'] == 0 or row['ttc'] > 1.95):
            if index + 1 in temp_df.index and (temp_df.loc[index + 1, 'ttc'] - row['ttc']) > 0:
                upper_bound = index + 1
                upper_bound_found = True
                return upper_bound, upper_bound_found
    
    return upper_bound, upper_bound_found

# function to find the upper bound based on brake and steering values
def find_upper_bound_brake_steering(temp_df, speed_threshold=None):
    start = False
    upper_bound_found = False
    upper_bound = None  # Default value if no upper bound is found
    for index, row in temp_df.iterrows():
        if row['brake'] > 0 or abs(row['steering']) >= 7.00:
            start = True
            
        elif start and (speed_threshold is None or row['speed'] < speed_threshold) and (row['brake'] == 0 or abs(row['steering']) < 7.00):
            upper_bound = index
            start = False
            upper_bound_found = True
            return upper_bound, upper_bound_found
    return upper_bound, upper_bound_found

print(f"{'Upper Bound':<15}{'Lower Bound':<15}")
print("-" * 30)

# Go through each of the 27 dataframes
for i, df in enumerate(dataframes):
    first_index = 0 
    last_index = 0
    upper_bound = 0
    lower_bound = 0

    """
    Find out the upper and lower bounds for the 27 crashes in the data set.
    ## Input: dataset
    ## Output : upper bound and lower bound values
    """

    for index, row in df.iloc[0:].iterrows():
        # Extract the current speed value from the 'speed' column for the current row
        current_speed = row['speed']
        if index + 1 in df.index:  # Ensure the next index exists
            next_speed = df.loc[index + 1, 'speed'] # speed value in the next row
            if is_speed_decreasing(current_speed, next_speed): # Finding first row where the speed is less than 15.99 (step 2)
                first_index = index   
                break
    
    # If somehow the participant didn’t slow down below 15.99, instead, find the first row where the |steering input| >= 7.0
    if first_index == 0: 
        for index, row in df.iloc[0:].iterrows():
            if abs(row['steering']) >= 7.0 and (row['time'] > 2): # checks for steering input greater than 7.0 after 2 seconds
                first_index = index
                break
    
    """
    identify End of Event (Post-Takeover):

        Either speed ≤ 0.9 OR speed increases by ≥ 1.00 (acceleration ≥ 1.00)s
    """
    if first_index not in df.index:
        print(f"Error: first_index {first_index} is out of bounds for the DataFrame. Skipping this DataFrame.")
        continue

    for index, row in df.loc[first_index:].iterrows():
        if row['speed'] <= 0.9:
            last_index = index - 1  # Subtract 1 to reference the last valid row before the condition fails
            break
    if last_index == 0: # If the last index is still 0, it means we didn't find a speed <= 0.9
        for index, row in df.loc[first_index:].iterrows():
            acceleration = round((row['speed'] - df.loc[index - 50, 'speed']) / (row['time'] - df.loc[index - 50, 'time']), 6) if index - 50 in df.index else 0  # 50 rows before the current index; approximately 1 second
            if acceleration >= 1.0:
                last_index = index
                break
            elif acceleration >= 0: # check for positive acceleration
                last_index = index
                break
            else:
                last_index = df.index[-1] # If no valid last index is found, set it to the last index of the DataFrame
                break
    lower_bound = last_index
    
    """
    Finding the upper bound
    Finding first row where the TTC value was 1.95 or less. 
    """

    # This creates a new DataFrame with the rows from the first row of the sub data frame to the first_index in reverse order
    # For going up the rows from the start point we found in step 2
    temp_df = df.loc[:first_index].iloc[::-1]

    start = False # Variable to track if we are in the range of interest
    upper_bound_found = False # Variable to track if we have found the upper bound

    for func, threshold in [(find_upper_bound_ttc, 17.0),
                            (find_upper_bound_ttc, None), # If the loop ends without finding a valid upper bound
                            (find_upper_bound_brake_steering, 17.0), # If the loop ends without finding a valid upper bound
                            (find_upper_bound_brake_steering, None)]: # If the loop ends without finding a valid upper bound
        if not upper_bound_found:
            upper_bound, upper_bound_found = func(temp_df, speed_threshold=threshold)    
    
    if not upper_bound_found: # Edge case: if there is no row with speed < 15.99, select the row which satisfies the TTC crieteria
        for index, row in df[::-1].iterrows():
            if row['ttc'] > 0 and row['ttc'] <= 1.95:
                start = True 
            elif start and index < first_index and (row['ttc'] == 0 or row['ttc'] > 1.95):
                if index + 1 in df.index and (df.loc[index + 1, 'ttc'] - row['ttc']) > 0:
                    upper_bound = index + 1
                    start = False
                    upper_bound_found = True
                    break
    
    # printing the upper and lower bounds
    if upper_bound_found:
        print(f"{upper_bound - 5:<15}{lower_bound:<15}")
    else:
        print(f"{0:<15}{lower_bound:<15}")