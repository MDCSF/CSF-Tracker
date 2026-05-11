import streamlit as st
import pandas as pd
from datetime import date
from pyairtable import Table

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

# --- 1. CONNECTION ---
# This tells the app to look in the "Secrets" box you just filled out
api_key = st.secrets["AIRTABLE_API_KEY"]
base_id = st.secrets["AIRTABLE_BASE_ID"]
table_name = st.secrets["AIRTABLE_TABLE_NAME"]
at_table = Table(api_key, base_id, table_name)

@st.cache_data(ttl=5)
def load_live_data():
    try:
        records = at_table.all()
        data = [{**rec.get('fields', {}), 'airtable_id': rec.get('id')} for rec in records]
        return pd.DataFrame(data)
    except Exception as e:
        # This will tell us if it's a 404 (Table/Base name wrong) or 401 (Token wrong)
        st.error(f"🔍 Connection Debugger: {e}")
        st.info("Check your Table Name in Airtable vs your Secrets. They must be identical.")
        return pd.DataFrame()

# --- 2. HEALTH & DASHBOARD ---
def get_health(row):
    today = date.today()
    deadline = row.get('Deadline')
    progress = row.get('Progress %', 0.0)
    if row.get('Status') == 'Completed' or progress >= 1.0: return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: return "🔴 OVERDUE"
    if pd.notnull(deadline) and (deadline - today).days <= 7: return "🟡 AT RISK"
    return "⚪ Pending"

df['Health'] = df.apply(get_health, axis=1)

# Position Health at Column 3 (Index 2)
cols = list(df.columns)
if 'Health' in cols:
    cols.insert(2, cols.pop(cols.index('Health')))
    df = df[cols]

st.title("🚀 CSF Global Action Dashboard")

# Visual Metrics
c1, c2, c3, c4 = st.columns(4)
h_counts = df['Health'].value_counts()
c1.metric("Total Items", len(df))
c2.metric("🔴 Overdue", h_counts.get("🔴 OVERDUE", 0))
c3.metric("🟡 At Risk", h_counts.get("🟡 AT RISK", 0))
c4.metric("Avg. Completion", f"{int(df['Progress %'].mean() * 100)}%")

# Bar Chart: Late Items by Owner
st.subheader("⚠️ Red Alert: Who is Late?")
overdue_df = df[df['Health'] == "🔴 OVERDUE"]
if not overdue_df.empty:
    st.bar_chart(overdue_df.groupby('Owner').size())
else:
    st.success("No overdue items! Great job team. ✅")

# --- 3. LIVE EDITOR ---
st.divider()
st.subheader("📝 Live Action Tracker")
st.info("💡 Edit the table and click 'Sync' below. No GitHub upload required!")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Health": st.column_config.TextColumn("Health", width="small"),
        "Progress %": st.column_config.NumberColumn("Progress (%)", format="%.2f", min_value=0, max_value=1),
        "Deadline": st.column_config.DateColumn("Deadline"),
        "Comments": st.column_config.TextColumn("Comments", width="large")
    }
)

# --- 4. THE SYNC BUTTON ---
if st.button("💾 Sync All Changes to Cloud"):
    with st.spinner("Updating CSF Cloud..."):
        for _, row in edited_df.iterrows():
            fields = row.drop('Health').drop('airtable_id', errors='ignore').to_dict()
            # Convert date to string for Airtable
            if fields.get('Deadline'): fields['Deadline'] = str(fields['Deadline'])
            
            if 'airtable_id' in row and pd.notnull(row['airtable_id']):
                at_table.update(row['airtable_id'], fields)
            else:
                at_table.create(fields)
        
        st.success("Changes Saved Permanently! Dashboard Updated.")
        st.cache_data.clear()
        st.rerun()
