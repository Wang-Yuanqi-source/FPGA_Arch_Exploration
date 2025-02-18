import pandas as pd
import numpy as np  # 用于处理 NaN 值

# Define the load_switch_dict function to load and structure the data into a dictionary
def load_switch_dict(file_path):
    # Load the data from the CSV file
    df = pd.read_csv(file_path)
    
    # Create a dictionary to store the switch data
    switch_dict = {}
    
    # Iterate over the DataFrame and populate the dictionary
    for _, row in df.iterrows():
        # If 'num_inputs' is empty, set it to the default value of 100
        num_inputs = row['num_inputs'] if pd.notna(row['num_inputs']) else 100
        key = (row['name'], num_inputs)
        value = row['delay']
        switch_dict[key] = value
    
    return switch_dict

# Modify the query_tdel function to raise an exception if no value is found
def query_tdel(switch_dict, name, num_inputs):
    # First, check if the exact match (name, num_inputs) exists
    if (name, num_inputs) in switch_dict:
        return switch_dict[(name, num_inputs)]
    
    # If num_inputs is NaN, it means the delay is the same for all inputs
    if (name, 100) in switch_dict:
        return switch_dict[(name, 100)]
    
    # If no matching key is found, raise an exception
    raise ValueError(f"No delay value found for switch '{name}' with {num_inputs} inputs.")
