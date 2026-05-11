import streamlit as st
import pandas as pd
from datetime import date
from pyairtable import Table

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

# --- 1. SMART HEALTH LOGIC ---
def get_health(row):
    today = date.today()
    deadline = row.get('Deadline')
    
    # Airtable Percent columns store 100% as 1.0
    try:
        progress = float(row.get('Progress %', 0.0))
    except:
        progress = 0.0

    status = str(row.get('Status', '')).strip()

    # If status is Completed OR progress is 100% (1.0)
    if status == 'Completed' or progress >= 1.0: 
        return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: 
        return "🔴 OVERDUE"
    if pd.notnull(deadline) and (pd.to_datetime(deadline).date() - today).days <= 7: 
        return "🟡 AT RISK"
    return "⚪ Pending"

@st.cache_data(ttl=5)
def load_live_data():
    try:
        # Pulling keys from your Streamlit Secrets
        at_table = Table(st.secrets["AIRTABLE_API_KEY"], st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        records = at_table.all()
        data = [{**rec.get('fields', {}), 'airtable_id': rec.get('id')} for rec in records]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Airtable Connection Error: {e}")
        return pd.DataFrame()

# --- 2. DATA PREP ---
df = load_live_data()

if not df.empty:
    # Ensure Progress is treated as a decimal (0.0 to 1.0)
    if 'Progress %' in df.columns:
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
    
    # Ensure Deadline is a date object
    if 'Deadline' in df.columns:
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date

    # Apply the Health logic
    df['Health'] = df.apply(get_health, axis=1)

    # Clean up column order for the Manager
    col_order = ['Task ID', 'Task Description', 'Health', 'Owner', 'Priority', 'Deadline', 'Status', 'Progress %', 'Comments', 'airtable_id']
    df = df[[c for c in col_order if c in df.columns]]

    # --- 3. SIDEBAR FILTERS ---
    st.sidebar.header("Dashboard Filters")
    owners = sorted(df['Owner'].dropna().unique().tolist())
    selected_owners = st.sidebar.multiselect("View by Owner", options=owners, default=owners)
    
    filtered_df = df[df['Owner'].isin(selected_owners)]

    # --- 4. THE DASHBOARD ---
    st.title("🚀 CSF Global Action Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    h_counts = filtered_df['Health'].value_counts()
    
    # Calculate average progress (showing as a clean percentage)
    avg_progress = filtered_df['Progress %'].mean() 

    m1.metric("Total Tasks", len(filtered_df))
    m2.metric("🔴 Overdue", h_counts.get("🔴 OVERDUE", 0))
    m3.metric("🟡 At Risk", h_counts.get("🟡 AT RISK", 0))
    m4.metric("Avg. Progress", f"{int(avg_progress * 100)}%")

    st.divider()

    # --- 5. THE DATA EDITOR ---
    st.subheader("📝 Live Tracker")
    st.caption("Double-click a cell to edit. Percentages should be entered as decimals (e.g., 0.5 for 50%).")
    
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Health": st.column_config.TextColumn("Health", width="small"),
            "Progress %": st.column_config.NumberColumn("Progress", format="%.0f%%", min_value=0, max_value=1),
            "Deadline": st.column_config.DateColumn("Deadline"),
            "airtable_id": None # Keep this hidden
        }
    )

    # --- 6. SYNC BUTTON ---
    if st.button("💾 Sync Changes to Airtable"):
        at_table = Table(st.secrets["AIRTABLE_API_KEY"], st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        with st.spinner("Pushing updates to cloud..."):
            for _, row in edited_df.iterrows():
                fields = row.drop(['Health', 'airtable_id'], errors='ignore').dropna().to_dict()
                
                # Convert date back to string for Airtable
                if fields.get('Deadline'): 
                    fields['Deadline'] = str(fields['Deadline'])
                
                # Sync logic
                if 'airtable_id' in row and pd.notnull(row['airtable_id']):
                    at_table.update(row['airtable_id'], fields)
                else:
                    at_table.create(fields)
                    
            st.success("Cloud Sync Complete!")
            st.cache_data.clear()
            st.rerun()

else:
    st.info("Awaiting data connection...")
