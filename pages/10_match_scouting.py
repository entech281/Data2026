
import streamlit as st
from streamlit_extras.row import row
from pages_util.style import st_horizontal

RECORD_KEY="scout_record"
class ScoutingRecord(object):
    def __init__(self):
        self.L1success = 0
        self.L2fails = 0

st.markdown(
    """
    <style>
    /* Target number input fields */
    input[type="number"] {
        width: 35px;
    }
    input[type="text"]{
        width: 70px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if RECORD_KEY in st.session_state:
    rec = st.session_state[RECORD_KEY]
else:
    rec = ScoutingRecord()
    st.session_state[RECORD_KEY] = rec

def add_L1_fail():
    rec.L2fails += 1

def add_L1_success():
    rec.L1success += 1

st.header("Scouting Form")
with st.form("match_record"):

    #this works, but the fields still verticalize on a phone
    #row1 = row(3,vertical_align="center")
    #row1.text_input("scout",max_chars=2)
    #row1.selectbox("Match",("Q1","Q2","Q3","Q4"))
    #row1.selectbox("Team", ("281", "4451", "342", "343"))

    with st_horizontal():
        st.text_input("scout",max_chars=2,key='aa')
        st.selectbox("Match",("Q1","Q2","Q3","Q4"),key='ab')
        st.selectbox("Team", ("281", "4451", "342", "343"),key='ac')
    st.divider()

    with st_horizontal():
        st.checkbox("Move")
        st.number_input(label="Coral",key='qqqf',min_value=1,max_value=50,step=1)

    st.divider()
    with st_horizontal():
        st.number_input(label="✅ L1 Coral",key='f',min_value=1,max_value=50,step=1)
        st.number_input(label="✅ L2 Coral",key='t',min_value=1,max_value=50,step=1)
        st.number_input(label="✅ L3 Coral",key='ttt',min_value=1,max_value=50,step=1)
        st.number_input(label="✅ L4 Coral",key='ssss',min_value=1,max_value=50,step=1)

    with st_horizontal():
        st.number_input(label="❌ L1 Coral",key='af',min_value=1,max_value=50,step=1)
        st.number_input(label="❌ L2 Coral",key='at',min_value=1,max_value=50,step=1)
        st.number_input(label="❌ L3 Coral",key='attt',min_value=1,max_value=50,step=1)
        st.number_input(label="❌ L4 Coral",key='assss',min_value=1,max_value=50,step=1)

    with st_horizontal():
        st.number_input(label="Algae Dislodge",key='bf',min_value=1,max_value=50,step=1)
        st.number_input(label="Algae Process",key='bt',min_value=1,max_value=50,step=1)
        st.number_input(label="Algae Barge",key='bttt',min_value=1,max_value=50,step=1)

    with st_horizontal():
        st.number_input(label="Penalties",key='baaf',min_value=1,max_value=50,step=1)


    st.divider()
    options = ["Park", "Shallow", "Deep"]

    with st_horizontal():
        st.checkbox("Ground Pickup")
        st.checkbox("amazing thing")
    st.divider()
    selection = st.segmented_control(
        "End Game", options, selection_mode="single"
    )

    st.divider()
    f = st.form_submit_button("Submit")
    if f:
        print (f"ScoutingRecord: Fails={rec.L2fails}, success={rec.L1success}")
        st.session_state[RECORD_KEY] = ScoutingRecord()