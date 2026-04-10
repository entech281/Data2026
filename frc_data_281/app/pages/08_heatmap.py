import streamlit as st
from frc_data_281.analysis import opr as opr3
from frc_data_281.app.components.event_selector import event_selector

st.set_page_config(layout="wide")


st.title("Z-score Heatmap")

selected_event = event_selector()
df = opr3.get_ccm_data_for_event(selected_event)
df = opr3.select_z_score_columns(df, ['team_id'])

# Drop noisy/granular columns not useful for the heatmap
cols_to_drop = [c for c in df.columns if
                'g206_penalty' in c or
                any(f'shift{i}' in c for i in range(1, 5))]
df = df.drop(columns=cols_to_drop)

df.reset_index(drop=True, inplace=True)
df = df.set_index('team_id')
df = df.T
df = df.sort_index()


def style_dataframe(df):
    return df.style.set_table_styles(
        [{
            'selector': 'th',
            'props': [
                ('background-color', '#4CAF50'),
                ('color', 'white'),
                ('font-family', 'Arial, sans-serif'),
                ('font-size', '10px')
            ]
        },
            {
                'selector': 'td',
                'props': [
                    ('font-size', '8px')
                ]
            }

        ]
    )


st.markdown(
    "<p style='font-size: 1.1rem; color: gray;'>"
    "⚠️ Z-scores for foul and opponent metrics (foul count, foul points, tech foul count, "
    "opponent score, opponent RP) have been <b>negated</b> so that green always means 'good' "
    "and red always means 'bad' across all columns."
    "</p>",
    unsafe_allow_html=True,
)

styled_df = style_dataframe(df)
styled_df = df.style.background_gradient(cmap='RdYlGn', vmin=-3.0, vmax=3.0)
styled_df.format("{:.2f}")

st.write(styled_df.to_html(), unsafe_allow_html=True)
