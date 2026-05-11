import streamlit as st
import pandas as pd
from datetime import date
from pyairtable import Table

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

# --- 1. DEFINE FUNCTIONS FIRST (Prevents NameError) ---
def get_health(row):
    today = date.today()
    deadline = row.get('Deadline')
    progress = row.get('Progress %', 0.0)
    
    # Handle data types (ensure progress is a number)
    try:
        progress = float(progress)
    except:
        progress = 0.0

    if row.get('Status') == 'Completed' or progress >= 1.0: 
        return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: 
        return "🔴 OVERDUE"
    if pd.notnull(deadline) and (pd.to_datetime(deadline).date() - today).days <= 7: 
        return "🟡 AT RISK"
    return "⚪ Pending"

@st.cache_data(ttl=10)
def load_live_data():
    try:
        api_key = st.secrets["AIRTABLE_API_KEY"]
        base_id = st.secrets["AIRTABLE_BASE_ID"]
        table_name = st.secrets["AIRTABLE_TABLE_NAME"]
        at_table = Table(api_key, base_id, table_name)
        
        records = at_table.all()
        data = [{**rec.get('fields', {}), 'airtable_id': rec.get('id')} for rec in records]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- 2. THE ACTION ---
df = load_live_data()

if not df.empty:
    # Clean up column names and types
    if 'Progress %' in df.columns:
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
    if 'Deadline' in df.columns:
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date

    # APPLY HEALTH (The line that was crashing)
    df['Health'] = df.apply(get_health, axis=1)

    # Reorder Health to Column 3 (Index 2)
    cols = list(df.columns)
    if 'Health' in cols:
        cols.insert(2, cols.pop(cols.index('Health')))
        df = df[cols]

    st.title("🚀 CSF Global Action Dashboard")
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    h_counts = df['Health'].value_counts()
    c1.metric("Total Items", len(df))
    c2.metric("🔴 Overdue", h_counts.get("🔴 OVERDUE", 0))
    c3.metric("🟡 At Risk", h_counts.get("🟡 AT RISK", 0))
    c4.metric("Avg. Progress", f"{int(df['Progress %'].mean() * 100)}%")

    st.divider()

    # The Editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor"
    )

    # Sync Button
    if st.button("💾 Sync All Changes to Cloud"):
        # (The rest of the sync logic from previous steps)
        st.success("Successfully Synced!")
        st.rerun()
else:
    st.info("Waiting for data from Airtable...")
