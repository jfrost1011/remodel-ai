import pandas as pd
import numpy as np
# Load data
df = pd.read_csv('../cleaned_remodeling_data_1000.csv')
def standardize_location(location):
    location = str(location).strip().title()
    if location.upper() in ['LA', 'LOS ANGELES', 'L.A.']:
        return 'Los Angeles'
    elif location.upper() in ['SD', 'SAN DIEGO']:
        return 'San Diego'
    elif 'Los Angeles' in location:
        return 'Los Angeles'
    elif 'San Diego' in location:
        return 'San Diego'
    return location
def standardize_project_type(project_type):
    project_type = str(project_type).strip().lower()
    type_mapping = {
        'kitchen': 'kitchen_remodel',
        'bathroom': 'bathroom_remodel',
        'bath': 'bathroom_remodel',
        'addition': 'room_addition',
        'room addition': 'room_addition',
        'whole house': 'whole_house_remodel',
        'complete': 'whole_house_remodel',
        'adu': 'accessory_dwelling_unit',
        'accessory dwelling': 'accessory_dwelling_unit',
        'landscape': 'landscaping',
        'landscaping': 'landscaping',
        'pool': 'pool_installation',
        'garage': 'garage_conversion',
        'garage conversion': 'garage_conversion',
        'roof': 'roofing',
        'roofing': 'roofing',
        'floor': 'flooring',
        'flooring': 'flooring'
    }
    for key, value in type_mapping.items():
        if key in project_type:
            return value
    return project_type.replace(' ', '_')
# Clean the data
df['Location'] = df['Location'].apply(standardize_location)
df['Remodel Type'] = df['Remodel Type'].apply(standardize_project_type)
df['Average Cost (High)'] = df['Average Cost (High)'].astype(float)
# Add calculated fields
df['Average Cost'] = (df['Average Cost (Low)'] + df['Average Cost (High)']) / 2
df['Cost Spread'] = df['Average Cost (High)'] - df['Average Cost (Low)']
df['is_california'] = df['Location'].isin(['San Diego', 'Los Angeles'])
# Filter for California projects
ca_df = df[df['Location'].isin(['San Diego', 'Los Angeles'])]
# Save cleaned data
df.to_csv('../processed/cleaned_data_all.csv', index=False)
ca_df.to_csv('../processed/cleaned_data_ca_only.csv', index=False)
print(f"Total projects after cleaning: {len(df)}")
print(f"California (SD/LA) projects: {len(ca_df)}")
print(f"\nLocation distribution after cleaning:")
print(df['Location'].value_counts().head(10))
print(f"\nProject type distribution after cleaning:")
print(df['Remodel Type'].value_counts().head(10))