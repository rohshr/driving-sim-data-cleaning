import pandas as pd

def split_csv_by_headers(file_path, headers):
    """
    Splits a CSV file into multiple DataFrames based on rows where the headers appear as values.

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
        normalized_data = data.applymap(lambda x: str(x).strip().lower() if isinstance(x, str) else x)

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
            dataframes.append(section)

        return dataframes

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Example usage
file_path = 'participant3.csv'
headers = ['time', 'throttle', 'brake', 'steering', 'speed', 'ttc']
dataframes = split_csv_by_headers(file_path, headers)

# Print the number of DataFrames and their first few rows
for i, df in enumerate(dataframes):
    print(f"DataFrame {i + 1}:")
    print(df.head())
    print(f"Original Index Range: {df.index.min()} to {df.index.max()}")
    
print(f"Total DataFrames created: {len(dataframes)}")