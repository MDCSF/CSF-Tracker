import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

st.set_page_config(page_title="CSF Global Action Tracker", layout="wide")

# --- 1. DATA LOADING & CLEANING ---
@st.cache_data
def load_data():
    try:
        # Load data skipping the title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df.columns = df.columns.str.strip()
        
        # Remove columns 8 and 9 (index 7 and 8) if they exist
        # We keep only: Task ID, Description, Owner, Deadline, Status, Priority, Progress %, Comments
        cols_to_keep = [c for i, c in enumerate(df.columns) if i not in [7, 8]]
        df = df[cols_to_keep]

        # Standardize Progress
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
        if df['Progress %'].max() > 1.0:
            df['Progress %'] = df['Progress %'] / 100.0
            
        # Standardize Deadlines
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
        
        return df
    except Exception as e:
        st.error(f"Error loading tracker: {e}")
        return None

if 'main_df' not in st.session_state:
    st.session_state.main_df = load_data()

df = st.session_state.main_df

# --- 2. LOGIC FOR HEALTH & ALERTS ---
def get_health(row):
    today = date.today()
    deadline = row['Deadline']
    progress = row['Progress %']
    if row['Status'] == 'Completed' or progress >= 1.0: return "🟢 Done"
    if pd.notnull(deadline) and deadline < today: return "🔴 OVERDUE"
    if pd.notnull(deadline) and (deadline - today).days <= 7: return "🟡 AT RISK"
    return "⚪ Pending"

df['Health'] = df.apply(get_health, axis=1)

# --- 3. VISUAL DASHBOARD ---
st.title("🚀 CSF Action Dashboard")

# Top Row Metrics
c1, c2, c3, c4 = st.columns(4)
total_tasks = len(df)
overdue_tasks = df[df['Health'] == "🔴 OVERDUE"]
at_risk_tasks = df[df['Health'] == "🟡 AT RISK"]

c1.metric("Total Actions", total_tasks)
c2.metric("🔴 Overdue", len(overdue_tasks), delta_color="inverse")
c3.metric("🟡 At Risk", len(at_risk_tasks))
c4.metric("Avg. Completion", f"{int(df['Progress %'].mean() * 100)}%")

# Charts Row
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Task Status Distribution")
    fig = px.pie(df, names='Status', hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("⚠️ Red Alert: Who is Late?")
    if len(overdue_tasks) > 0:
        late_summary = overdue_tasks.groupby('Owner').size().reset_index(name='Late Tasks')
        fig_late = px.bar(late_summary, x='Owner', y='Late Tasks', color='Owner',
                         title="Overdue Tasks by Owner")
        st.plotly_chart(fig_late, use_container_width=True)
    else:
        st.success("No one is late! High performance mode active. ✅")

# --- 4. THE LIVE EDITOR ---
st.divider()
st.subheader("📝 Master Action Tracker")

# Filtering by Owner
owners = sorted(df['Owner'].dropna().unique().tolist())
selected_owner = st.sidebar.multiselect("Filter by Team Member", options=owners, default=owners)
filtered_df = df[df['Owner'].isin(selected_owner)]

edited_df = st.data_editor(
    filtered_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Health": st.column_config.TextColumn("Health", width="small"),
        "Progress %": st.column_config.NumberColumn("Progress (%)", format="%.2f", min_value=0, max_value=1),
        "Deadline": st.column_config.DateColumn("Deadline"),
        "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"]),
        "Priority": st.column_config.SelectboxColumn(options=["Low", "Medium", "High"]),
        "Comments": st.column_config.TextColumn("Comments", width="large")
    }
)

# --- 5. THE SYNC/SAVE BUTTON ---
st.divider()
if st.button("💾 Sync Changes & Download Master File"):
    # Updating the session state
    st.session_state.main_df = edited_df
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("Click here to Download Updated CSV for GitHub", data=csv, file_name='tracker_data.csv')
    st.success("Changes synced to dashboard! Remember to upload the downloaded file to GitHub to keep it permanent.")
