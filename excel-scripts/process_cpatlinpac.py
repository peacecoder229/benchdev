import os
import re
import pandas as pd



def extract_threads_and_performance(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()
    
    start_index = end_index = None
    for index, line in enumerate(content):
        if "Timing linear equation system solver" in line:
            start_index = index + 2  # Assuming the next line after this is the header
        elif ("Performance Summary (GFlops)" in line or line.startswith("Done:")) and start_index is not None:
            end_index = index
            break
    
    if start_index is None or end_index is None or start_index >= end_index:
        return [], []  # Return empty lists if the section is not found or is incorrectly parsed
    
    time_data = []
    gflops_data = []
    for line in content[start_index:end_index]:
        if line.strip() and "Time(s)" not in line and "Size" not in line:  # Skip header and empty lines
            parts = line.split()
            try:
                time_data.append(float(parts[3]))  # Ensure conversion to float is possible
                gflops_data.append(float(parts[4]))
            except ValueError:
                print(f"Warning: Skipping line due to error converting to float: {line}")
    
    return time_data, gflops_data

def extract_prefix(name):
    # This regex matches the first occurrence of the pattern \d+_\d+
    match = re.match(r'(\d+_\d+)', name)
    if match:
        return match.group(1)
    return None  # Return None or some default value if no match is found

def main(directory):
    times = {}
    gflops = {}
    result_EN = []
    result_Dis = []

    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                full_path = os.path.join(subdir, file)
                times_list, gflops_list = extract_threads_and_performance(full_path)
                #print(full_path)
                #print(gflops_list)

                filename = os.path.splitext(file)[0]
                # Simplify and standardize replacements
                filename = re.sub(r'lp_cpat_enabled_resctrl_0-59_0-59_\d+', 'lp_EN', filename)
                filename = re.sub(r'lp_cpat_disabled_resctrl_0-59_0-59_\d+', 'lp_Dis', filename)
                #filename = filename.replace('lp_cpat_enabled_resctrl_0-59_0-59', 'lp_EN')
                #filename = filename.replace('lp_cpat_disabled_resctrl_0-59_0-59', 'lp_Dis')
                filename = filename.replace('hp_cpat_enabled_resctrl_0-59_0-59_30', 'hp_EN')
                filename = filename.replace('hp_cpat_disabled_resctrl_0-59_0-59_30', 'hp_Dis')
                filename = filename.replace('hp_cpat_enabled_resctrl_0-59_30', 'hp-only')
                base_name = f"{os.path.basename(subdir)}_{filename}"

                gflops[base_name] = gflops_list

    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in gflops.items()]))

    # Assuming extract_prefix is defined to extract '30_xx' as prefixes
    #print(df.columns)
    unique_prefixes = set(extract_prefix(name) for name in df.columns if extract_prefix(name) is not None)

    for prefix in unique_prefixes:
        print(prefix)
        hp_en_col = f"{prefix}_hp_EN"
        lp_en_col = f"{prefix}_lp_EN"
        hp_dis_col = f"{prefix}_hp_Dis"
        lp_dis_col = f"{prefix}_lp_Dis"
        print(f"HP col {hp_en_col} LP col {lp_en_col}")
        # Collect and print directly to a list
        print(df.columns)
        if hp_en_col in df.columns and lp_en_col in df.columns:
            print(df[hp_en_col])
            print(df[lp_en_col])
            hp_en_avg = df[hp_en_col][1:-1].mean() if len(df[hp_en_col]) > 2 else None
            lp_en_avg = df[lp_en_col][1:-1].mean() if len(df[lp_en_col]) > 2 else None
            hp , lp = prefix.split("_")
            result_EN.append((hp, lp, hp_en_avg, lp_en_avg))

        if hp_dis_col in df and lp_dis_col in df:
            hp_dis_avg = df[hp_dis_col][1:-1].mean() if len(df[hp_dis_col]) > 2 else None
            lp_dis_avg = df[lp_dis_col][1:-1].mean() if len(df[lp_dis_col]) > 2 else None
            hp , lp = prefix.split("_")
            #result_Dis.append((prefix, hp_dis_avg, lp_dis_avg))
            result_Dis.append((hp, lp, hp_dis_avg, lp_dis_avg))

    # Write results directly to CSV
    with open('result_gflops_EN.csv', 'w') as f:
        f.write('HP,LP,HP_EN_Avg,LP_EN_Avg\n')
        for item in result_EN:
            f.write(f"{item[0]},{item[1]},{item[2]},{item[3]}\n")

    with open('result_gflops_Dis.csv', 'w') as f:
        #f.write('Prefix,HP_Dis_Avg,LP_Dis_Avg\n')
        f.write('HP,LP,,HP_Dis_Avg,LP_Dis_Avg\n')
        for item in result_Dis:
            f.write(f"{item[0]},{item[1]},{item[2]}, {item[3]}\n")

if __name__ == "__main__":
    directory = './'
    main(directory)

