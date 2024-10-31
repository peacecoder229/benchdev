import os
import re

def find_files(directory, file_pattern):
    """Find all files in a directory that match the compiled file_pattern."""
    pattern = re.compile(file_pattern)
    return [os.path.join(directory, f) for f in os.listdir(directory) if pattern.search(f)]

# Usage
directory = '.' # or the path to the directory where the files are located
file_pattern = 'bfloat16' # the pattern to search in the filenames
files = find_files(directory, file_pattern)
print(files)

