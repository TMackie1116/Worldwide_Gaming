#streamlit run /Users/tucker/Desktop/DataVizFinal/StreamLitFinal.py

import streamlit as st
import pandas as pd
import pydeck as pdk

st.title('Final Data Viewer')

# Load data
csv_path = 'final_data.csv'
df = pd.read_csv(csv_path)
print(df.shape)
print(df.columns)
print(df.head())
st.write('Data Preview:')
st.dataframe(df)

# Sidebar filter
platforms = df['platform'].unique()
selected_platform = st.sidebar.selectbox('Select Platform', platforms)
filtered_df = df[df['platform'] == selected_platform]

# Static country-to-lat/lon dictionary (for faster lookup)
country_coords = {
    'Germany': {'latitude': 51.1657, 'longitude': 10.4515},
    'United States': {'latitude': 37.0902, 'longitude': -95.7129},
    'Japan': {'latitude': 36.2048, 'longitude': 138.2529},
    'United Kingdom': {'latitude': 55.3781, 'longitude': -3.4360},
    # Add more if your data expands
}

# Add latitude/longitude columns
filtered_df['latitude'] = filtered_df['country'].map(lambda x: country_coords.get(x, {}).get('latitude'))
filtered_df['longitude'] = filtered_df['country'].map(lambda x: country_coords.get(x, {}).get('longitude'))

st.subheader('World Heatmap of Locations')

if filtered_df[['latitude', 'longitude']].dropna().shape[0] > 0:
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=filtered_df['latitude'].mean(),
            longitude=filtered_df['longitude'].mean(),
            zoom=2,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'HeatmapLayer',
                data=filtered_df.dropna(subset=['latitude', 'longitude']),
                get_position='[longitude, latitude]',
                aggregation='MEAN',
                opacity=0.7,
            ),
        ],
    ))
else:
    st.write('No location data available for selected platform.')
