import streamlit as st
import pandas as pd
from datetime import date
from pyairtable import Table

st.set_page_config(page_title="CSF Action Dashboard", layout="wide")

# --- 1. CORE LOGIC ---
def get_health(row):
    today = date.today()
    deadline = row.get('Deadline')
    status = str(row.get('Status', '')).strip()
    
    try:
        raw_p = float(row.get('Progress %', 0))
        progress = raw_p / 100.0 if raw_p > 1.0 else raw_p
    except:
        progress = 0.0

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
        at_table = Table(st.secrets["AIRTABLE_API_KEY"], st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        records = at_table.all()
        # Filter out empty rows
        data = [{**rec.get('fields', {}), 'airtable_id': rec.get('id')} for rec in records if rec.get('fields', {}).get('Task Description')]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- 2. DATA PROCESSING ---
df = load_live_data()

if not df.empty:
    df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
    df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
    df['Health'] = df.apply(get_health, axis=1)

    # --- SIDEBAR ---
    st.sidebar.title("🚀 CSF Control")
    owners = sorted(df['Owner'].dropna().unique().tolist())
    selected_owners = st.sidebar.multiselect("Focus on Team Members:", options=owners, default=owners)
    f_df = df[df['Owner'].isin(selected_owners)]

    # --- 3. TOP LEVEL METRICS ---
    st.title("📊 CSF Global Action Dashboard")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    h_counts = f_df['Health'].value_counts()
    
    avg_p = f_df['Progress %'].apply(lambda x: x/100 if x > 1 else x).mean()

    m1.metric("Total Actions", len(f_df))
    m2.metric("🟢 Completed", len(f_df[f_df['Health'] == "🟢 Done"]))
    m3.metric("🔴 Overdue", h_counts.get("🔴 OVERDUE", 0))
    m4.metric("🟡 At Risk", h_counts.get("🟡 AT RISK", 0))
    m5.metric("Avg. Progress", f"{int(avg_p * 100)}%")

    st.divider()

    # --- 4. TEAM WORKLOAD SUMMARY (NEW SECTION) ---
    st.subheader("👥 Team Workload Breakdown")
    
    # Logic to create the per-person summary
    workload = f_df.groupby('Owner')['Health'].value_counts().unstack(fill_value=0)
    
    # Ensure all status columns exist in the summary
    for status in ["🟢 Done", "🔴 OVERDUE", "🟡 AT RISK", "⚪ Pending"]:
        if status not in workload.columns:
            workload[status] = 0
            
    # Calculate Total Tasks per person
    workload['Total'] = workload.sum(axis=1)
    
    # Sort by most overdue first to catch problems
    workload = workload.sort_values(by="🔴 OVERDUE", ascending=False)
    
    # Reorder columns for a clean look
    workload = workload[["Total", "🟢 Done", "⚪ Pending", "🟡 AT RISK", "🔴 OVERDUE"]]
    
    st.table(workload) # Display as a clean, static summary table

    st.divider()

    # --- 5. THE LIVE TRACKER ---
    st.subheader("📝 Live Action Items")
    col_order = ['Task ID', 'Task Description', 'Health', 'Owner', 'Priority', 'Deadline', 'Status', 'Progress %', 'airtable_id']
    display_df = f_df[[c for c in col_order if c in f_df.columns]]

    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Health": st.column_config.TextColumn("Health", width="small"),
            "Progress %": st.column_config.NumberColumn("Progress", format="%.0f%%"),
            "Deadline": st.column_config.DateColumn("Deadline"),
            "airtable_id": None 
        }
    )

    # --- 6. SYNC ---
    if st.button("💾 Sync Changes to Airtable"):
        at_table = Table(st.secrets["AIRTABLE_API_KEY"], st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        with st.spinner("Updating Cloud..."):
            for _, row in edited_df.iterrows():
                fields = row.drop(['Health', 'airtable_id'], errors='ignore').dropna().to_dict()
                if fields.get('Deadline'): fields['Deadline'] = str(fields['Deadline'])
                
                if 'airtable_id' in row and pd.notnull(row['airtable_id']):
                    at_table.update(row['airtable_id'], fields)
                else:
                    at_table.create(fields)
            st.success("Synced!")
            st.cache_data.clear()
            st.rerun()
else:
    st.info("Awaiting connection to Airtable...")
