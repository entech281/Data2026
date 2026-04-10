import streamlit as st
import plotly.graph_objects as go
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

st.markdown(
    "<p style='font-size: 1.1rem; color: gray;'>"
    "⚠️ Z-scores for foul and opponent metrics (foul count, foul points, tech foul count, "
    "opponent score, opponent RP) have been <b>negated</b> so that green always means 'good' "
    "and red always means 'bad' across all columns."
    "</p>",
    unsafe_allow_html=True,
)

# --- Heatmap with frozen column headers ---

styled_df = df.style.background_gradient(cmap='RdYlGn', vmin=-3.0, vmax=3.0)
styled_df.format("{:.2f}")
styled_df.set_table_styles([
    {'selector': 'th', 'props': [
        ('background-color', '#4CAF50'),
        ('color', 'white'),
        ('font-family', 'Arial, sans-serif'),
        ('font-size', '10px'),
        ('position', 'sticky'),
        ('top', '0'),
        ('z-index', '1'),
    ]},
    {'selector': 'td', 'props': [
        ('font-size', '8px'),
    ]},
])

table_html = styled_df.to_html()
st.markdown(
    f"<div style='max-height: 70vh; overflow-y: auto; border: 1px solid #ddd;'>"
    f"{table_html}"
    f"</div>",
    unsafe_allow_html=True,
)

# --- Team Z-Score Comparison Line Chart ---

st.subheader("Compare Team Z-Scores")

team_columns = [int(c) for c in df.columns]
selected_teams = st.multiselect(
    "Select teams to compare",
    options=sorted(team_columns),
    default=[],
    format_func=lambda t: f"Team {t}",
)

if selected_teams:
    fig = go.Figure()
    for team in selected_teams:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[team],
            mode='lines+markers',
            name=f"Team {team}",
        ))
    fig.update_layout(
        xaxis_title="Metric",
        yaxis_title="Z-Score",
        yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray'),
        hovermode='x unified',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Select teams above to see a z-score comparison chart.")
