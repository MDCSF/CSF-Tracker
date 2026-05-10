import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load data skipping the very first title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df.columns = df.columns.str.strip()
        
        # 1. Clean Progress (Ensure it is a decimal 0.0 - 1.0)
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
        
        # 2. Clean Deadlines
        df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
        
        # 3. Apply the Color Coding Logic
        def apply_status_color(row):
            today = date.today()
            deadline = row['Deadline']
            progress = row['Progress %']
            status = row['Status']
            
            # Rule 1: Green if Completed
            if status == 'Completed' or progress >= 1.0:
                return "🟢 On Track / Done"
            
            # Rule 2: Red if Past Deadline and not 100%
            if pd.notnull(deadline) and deadline < today and progress < 1.0:
                return "🔴 OVERDUE"
            
            # Rule 3: Yellow if Deadline is close (within 7 days) and progress < 50%
            if pd.notnull(deadline) and (deadline - today).days <= 7 and progress < 0.5:
                return "🟡 AT RISK"
            
            return "⚪ Pending"

        df.insert(0, 'Health', df.apply(apply_status_color, axis=1))
        
        return df
    except Exception as e:
        st.error(f"Data loading error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- DASHBOARD ---
    st.subheader("📊 Performance Health")
    c1, c2, c3, c4 = st.columns(4)
    health_counts = df['Health'].value_counts()
    
    c1.metric("Overdue (Red)", health_counts.get("🔴 OVERDUE", 0))
    c2.metric("At Risk (Yellow)", health_counts.get("🟡 AT RISK", 0))
    c3.metric("On Track (Green)", health_counts.get("🟢 On Track / Done", 0))
    c4.metric("Avg. Completion", f"{int(df['Progress %'].mean() * 100)}%")

    # --- TRACKER ---
    st.divider()
    current_owners = sorted(df['Owner'].dropna().unique().tolist())
    st.sidebar.header("Filter View")
    selected_owner = st.sidebar.multiselect("Owner", options=current_owners, default=current_owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)]

    st.subheader("📝 Live Tracker")
    st.caption("🔴 = Past Deadline | 🟡 = Due soon & < 50% | 🟢 = Done")

    st.data_editor(
        filtered_df,
        num_rows="dynamic",
        column_config={
            "Health": st.column_config.TextColumn("Health", width="medium"),
            "Deadline": st.column_config.DateColumn("Deadline", format="YYYY-MM-DD"),
            "Progress %": st.column_config.NumberColumn(
                "Progress (%)",
                min_value=0.0,
                max_value=1.0,
                format="%.2f" 
            ),
            "Status": st.column_config.SelectboxColumn(
                options=["Not Started", "In Progress", "Completed", "On Hold"]
            ),
        },
        hide_index=True,
        use_container_width=True
    )

    # --- DOWNLOAD ---
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Updated Tracker", data=csv, file_name='csf_tracker.csv', mime='text/csv')
