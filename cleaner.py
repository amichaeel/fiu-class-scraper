import pandas as pd
import sys
import os
from io import StringIO

def expand_complex_class_data(df):
    expanded_data = []
    for index, row in df.iterrows():
        dates = [d.strip() for d in str(row['dates']).split('\n')]
        locations = [l.strip() for l in str(row['location']).split('\n')]
        times = [t.strip() for t in str(row['time']).split('\n')]
        instructors = [i.strip() for i in str(row['instructors']).split('\n')]
        for date, location, time, instructor in zip(dates, locations, times, instructors):
            new_row = row.copy()
            new_row['dates'] = date
            new_row['location'] = location
            new_row['time'] = time
            new_row['instructors'] = instructor
            expanded_data.append(new_row)
    return pd.DataFrame(expanded_data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleaner.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist in the directory {os.getcwd()}.")
        sys.exit(1)
        
    df = pd.read_csv(filename)
    expanded_df = expand_complex_class_data(df)
    expanded_df.to_csv('cleaned_' + filename, index=False)
    print(f"Processed file saved as: cleaned_{filename}")
