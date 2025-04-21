# Guide to Using `sim_data_cleanup.py`

Script to extract crash data ranges from BeamNG driving simulator experiments.

## Step 0:
Create a CSV file which only contains the rows of timestamped data. Make sure the CSV files are in the same folder as the script

## Prerequisites
1. Ensure Python 3.x is installed on your system.
2. Install required dependencies by running:
    ```bash
    pip install -r requirements.txt
    ```
3. Place your raw simulation data files in the appropriate directory.

## Usage
Run the script from the command line with the following syntax:
```bash
python sim_data_cleanup.py [filename]
```

### Example
To clean a file named `raw_data.csv`:
```bash
python sim_data_cleanup.py raw_data.csv
```
