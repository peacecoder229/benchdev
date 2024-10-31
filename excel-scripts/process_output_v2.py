import os
import re
import csv

def extract_threads_and_performance(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()
    
    # Find start and end indices for the performance data
    start_index = end_index = None
    for index, line in enumerate(content):
        if "Timing linear equation system solver" in line:
            start_index = index + 2  # Skip the header line
        elif "Performance Summary (GFlops)" in line and start_index is not None:
            end_index = index
            break
    
    if start_index is None or end_index is None:
        return None, [], []
    
    # Extract number of threads
    threads = None
    for line in content:
        if "Number of threads:" in line:
            threads = re.search(r"Number of threads: (\d+)", line).group(1)
            break
    
    # Process the table data
    time_data = []
    gflops_data = []
    for line in content[start_index:end_index]:
        if line.strip():  # Avoid empty lines
            parts = line.split()
            time_data.append(parts[3])
            gflops_data.append(parts[4])
    
    return threads, time_data, gflops_data

def concatenate_data(data_list):
    return ", ".join(data_list)

def main(directory):
    all_data = {}
    
    # Walk through each directory and file
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                full_path = os.path.join(subdir, file)
                result = extract_threads_and_performance(full_path)
                if result:
                    threads, times, gflops = result
                    # Modify file name for column headers
                    filename = os.path.splitext(file)[0]
                    filename = filename.replace('lp_cpat_enabled_resctrl_0-59_0-59', 'lp_EN')
                    filename = filename.replace('lp_cpat_disabled_resctrl_0-59_0-59', 'lp_Dis')
                    filename = filename.replace('hp_cpat_enabled_resctrl_0-59_0-59_30', 'hp_EN')
                    filename = filename.replace('hp_cpat_disabled_resctrl_0-59_0-59_30', 'hp_Dis')
                    filename = filename.replace('hp_cpat_enabled_resctrl_0-59_30', 'hp-only')
                    #base_name = f"{os.path.basename(subdir)}_{filename}_Threads_{threads}"
                    base_name = f"{os.path.basename(subdir)}_{filename}"
                    all_data[f"{base_name}_GFlops"] = concatenate_data(gflops)
                    all_data[f"{base_name}_Time(s)"] = concatenate_data(times)
    
    # Writing to CSV
    with open('result_mod.csv', 'w', newline='') as csvfile:
        fieldnames = sorted(all_data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        # Write the data as a single row
        writer.writerow(all_data)

if __name__ == "__main__":
    directory = './'  # Set this to your directories path
    main(directory)

