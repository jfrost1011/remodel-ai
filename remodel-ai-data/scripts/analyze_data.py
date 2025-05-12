import pandas as pd
import sys
import os
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load data
df = pd.read_csv('../cleaned_remodeling_data_1000.csv')
print(f"Total projects: {len(df)}")
print(f"\nUnique locations: {df['Location'].nunique()}")
print(f"Location distribution:")
print(df['Location'].value_counts().head(10))
print(f"\nUnique remodel types: {df['Remodel Type'].nunique()}")
print(f"Remodel type distribution:")
print(df['Remodel Type'].value_counts().head(10))
print(f"\nCost statistics:")
print(f"Min low cost: ${df['Average Cost (Low)'].min():,.0f}")
print(f"Max high cost: ${df['Average Cost (High)'].max():,.0f}")
print(f"Average spread: ${(df['Average Cost (High)'] - df['Average Cost (Low)']).mean():,.0f}")
# Check for California cities
ca_cities = ['San Diego', 'Los Angeles', 'LA', 'SD']
ca_projects = df[df['Location'].str.upper().isin([city.upper() for city in ca_cities])]
print(f"\nCalifornia projects (SD/LA): {len(ca_projects)}")
print(f"Other locations: {len(df) - len(ca_projects)}")
# Save unique values
locations = df['Location'].unique()
with open('../processed/unique_locations.txt', 'w') as f:
    for loc in sorted(locations):
        f.write(f"{loc}\n")
project_types = df['Remodel Type'].unique()
with open('../processed/unique_project_types.txt', 'w') as f:
    for pt in sorted(project_types):
        f.write(f"{pt}\n")