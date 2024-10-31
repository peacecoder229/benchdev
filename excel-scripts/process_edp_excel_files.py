import os
import re
import argparse
import pandas as pd

def find_files(directory, file_pattern):
    """Find all files in a directory that match the file_pattern."""
    pattern = re.compile(file_pattern)
    return [os.path.join(directory, f) for f in os.listdir(directory) if pattern.search(f)]



def extract_metrics_from_file(file_path, sheet_name, metrics_with_columns):
    """Extract specified metrics and their specified columns from an Excel file."""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0, engine='openpyxl')
        extracted_data = {}
        for metric_with_column in metrics_with_columns:
            metric_name, column_name = metric_with_column.split(':::')
            value = df.loc[metric_name, column_name] if metric_name in df.index and column_name in df.columns else None
            extracted_data[metric_with_column] = value
        return extracted_data
    except Exception as e:
        print(f"An error occurred while processing file {file_path}: {e}")
        return None



def append_to_csv(data_row, outfile):
    """Append the data row to the CSV file."""
    if outfile:
        with open(outfile, 'a', newline='') as f:
            df = pd.DataFrame([data_row])
            df.to_csv(f, header=f.tell()==0, index=False)
    else:
        df = pd.DataFrame([data_row])
        print(df.to_csv(header=True, index=False))

def main(directory, file_pattern, metrics, sheet_name, outfile, metricfile):
    # Read metrics from a file if provided
    if metricfile:
        with open(metricfile, 'r') as f:
            metrics = f.read().strip().split(',')
    elif not metrics:
        raise ValueError("Either --metrics or --metricfile must be provided.")

    # Find all files that match the file_pattern
    files = find_files(directory, file_pattern)
    print(files)
    
    for file_path in files:
        # Extract metrics from file
        metrics_data = extract_metrics_from_file(file_path, sheet_name, metrics)
        if metrics_data is not None:
            # Prepare the data row for the CSV
            data_row = {'Filename': os.path.basename(file_path)}
            data_row.update(metrics_data)
            # Append the data row to the CSV file
            append_to_csv(data_row, outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract metrics from Excel files and compile them into a CSV file.')
    parser.add_argument('--directory', type=str, default='.', help='Directory to search for Excel files')
    parser.add_argument('--filepat', type=str, required=True, help='Regular expression for file search')
    parser.add_argument('--metrics', type=str, help='Comma separated list of metrics to extract')
    parser.add_argument('--sheetname', type=str, required=True, help='Name of the sheet to process')
    parser.add_argument('--outfile', type=str, help='Name of the output CSV file')
    parser.add_argument('--metricfile', type=str, help='File containing list of metrics')

    args = parser.parse_args()
    
    # Validate that one of --metrics or --metricfile is provided
    if not args.metrics and not args.metricfile:
        parser.error('Either --metrics or --metricfile must be provided.')

    # Call main function with the proper arguments
    main(args.directory, args.filepat, args.metrics.split(',') if args.metrics else None, args.sheetname, args.outfile, args.metricfile)

