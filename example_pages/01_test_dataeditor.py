import streamlit as st
from motherduck import con

TEST_TABLE = "scouting.test"
st.title("Demo Table Editor")
st.subheader("edit contents of table scouting.test in motherduck database")

st.caption("""This is a demo of editing the rows in a table.
not for end users, this builds a way to edit stuff for admins or developers
""")

# very subtle trick here. we're NOT selecting the timestamp column
# out so that it isnt visible or editable to users
# each row will get a default timestamp because the default value is "current_timestamp"
# see ddl.py
df = con.sql(f"select id, foo, bar from {TEST_TABLE}").df()

edited_df = st.data_editor(df, num_rows="dynamic")
confirm = st.button('Save Changes')


def get_removed_row_keys(original_df, edited_df, key_field):
    original_ids = set(df[key_field].tolist())
    edited_ids = set(edited_df[key_field].tolist())
    return original_ids - edited_ids


if confirm:

    # Note
    # it is a very bad idea to replace the whole table, even though there
    # are alot of shortcuts that do it that way.
    # that's bedause you lose any timestampes, and also you lose any
    # important schema definition info, like primary keys, which you
    # can see here is important to handle row updates
    con.sql(f"insert or replace into {TEST_TABLE} BY NAME SELECT * from edited_df ");

    removed_row_keys=get_removed_row_keys(df, edited_df,"id")

    for id in removed_row_keys:
        con.sql(f"delete from {TEST_TABLE} where id={id}")

    updated_or_inserted_count = len(edited_df) - len(removed_row_keys)
    deleted_row_count = len(removed_row_keys)
    st.success(f"Updated {updated_or_inserted_count} row, Deleted {deleted_row_count} rows", icon="✅")
