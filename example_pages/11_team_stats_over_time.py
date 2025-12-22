import streamlit as st
import pandas as pd
import opr3
st.set_page_config(layout="wide")


@st.cache_data( ttl=120)
def get_historical_match_data() :
    df = opr3.matches_over_time()  # Ensure your DataFrame has 'team_id' and z-score columns
    df.reset_index(drop=True, inplace=True)
    #df['team_id'] = df['team_id'].apply(str)
    return df

df = get_historical_match_data()

z_columns = [col for col in df.columns if col.endswith('_z')]
columns_to_keep = ['team_id'] + z_columns

# Group by team_id and aggregate all _z columns into lists per batch
# since soemtimes we can have n/a values, fill those values with zeros
result = df[columns_to_keep].fillna(0).groupby('team_id').agg(lambda x: list(x))

# Reset index for a cleaner output
result = result.reset_index()

def make_line_chart_col(col_name):

    return st.column_config.AreaChartColumn(
        col_name,
        width="medium",
        y_min=-4,
        y_max=4
    )

def make_column_config():
    d = {}
    for zc in z_columns:
        d[zc] = make_line_chart_col(zc)
    return d

cc = make_column_config()
cc['team_id'] = st.column_config.Column(
    "TeamID",
    pinned=True
)
st.dataframe(result,height=900,hide_index=True,column_config=cc)


