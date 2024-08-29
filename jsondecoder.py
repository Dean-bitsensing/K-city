import h5py
import json
import os
import matplotlib.pyplot as plt

# Path to .h5 file
directory = 'D:\cicd_test_dataset'
file_path = '20231219_110612_0063_192.168.102.80.h5'  # Change to file name

file_path = os.path.join(directory, file_path)

# Lists to store latitudes and longitudes
latitudes = []
longitudes = []

# Open the .h5 file
with h5py.File(file_path, 'r') as file:
    # Find groups that start with 'SCAN_'
    groups = [key for key in file.keys() if key.startswith('SCAN_')]
    
    for group in groups:
        group = file[group]
        # Read the 'Status' data
        status_data = group['Status'][:]
   
        # Decode the byte array to a string and parse the JSON
        status_json = json.loads(status_data.tobytes().decode('utf-8'))
        lat = status_json['gps']['latitude']
        long = status_json['gps']['longitude']
        
        # Append to the lists
        latitudes.append(lat)
        longitudes.append(long)

# Plotting the latitudes and longitudes
plt.figure(figsize=(10, 6))
plt.scatter(longitudes, latitudes, marker='o', color='blue')

# Label the axes
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Latitude vs Longitude')

# Display the plot
plt.grid(True)
plt.show()
