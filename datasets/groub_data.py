import pandas as pd
import glob
import os

def concatenate_csv_files(folder_path, output_file_name="combined_data.csv"):
    """
    Concatenates all CSV files in a given folder into a single DataFrame
    and saves it as a new CSV file.

    Args:
        folder_path (str): The path to the folder containing the CSV files.
        output_file_name (str): The name of the output CSV file (e.g., "combined_data.csv").
    """
    # Create a list to store individual DataFrames
    all_dataframes = []

    # Get a list of all CSV files in the specified folder
    # os.path.join handles path construction for different operating systems
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    # Loop through each CSV file, read it, and append to the list
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            all_dataframes.append(df)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Concatenate all DataFrames in the list
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        # Save the combined DataFrame to a new CSV file
        output_path = os.path.join(folder_path, output_file_name)
        combined_df.to_csv(output_path, index=False)
        print(f"All CSV files concatenated and saved to: {output_path}")
    else:
        print("No CSV files found in the specified folder.")

# Example usage:
# Replace 'your_folder_path_here' with the actual path to your folder
# containing the CSV files.
folder_to_process = "./"
concatenate_csv_files(folder_to_process, "master_combined.csv")