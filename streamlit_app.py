import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load and immediately skip the title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        
        # 1. Clean column names (REALLY important for matching 'Progress %')
        df.columns = df.columns.str.strip()
        
        # 2. FORCE PROGRESS EXTRACTION
        # We convert to string first, remove any % signs, then turn back to number
        if 'Progress %' in df.columns:
            df['Progress %'] = df['Progress %'].astype(str).str.replace('%', '')
            df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
            
            # If the CSV has whole numbers (like 75), convert them to decimals (0.75)
            # Streamlit's editor prefers 0.0 - 1.0 for percentage bars/logic
            df.loc[df['Progress %'] > 1, 'Progress %'] = df['Progress %'] / 100
        
        # 3. CLEAN DEADLINES
        if 'Deadline' in df.columns:
            df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
        
        # 4. APPLY HEALTH LOGIC (🔴, 🟡, 🟢)
        def get_health(row):
            today = date.today()
            deadline = row.get('Deadline')
            progress = row.get('Progress %', 0)
            status = str(row.get('Status', '')).strip()
            
            if status == 'Completed' or progress >= 1.0:
                return "🟢 Done"
            if pd.notnull(deadline) and deadline < today and progress < 1.0:
                return "🔴 OVERDUE"
            if pd.notnull(deadline) and (deadline - today).days <= 7 and progress < 0.5:
                return "🟡 AT RISK"
            return "⚪ Pending"

        # Insert Health at the very beginning
        health_col = df.apply(get_health, axis=1)
        if 'Health' in df.columns:
            df['Health'] = health_col
        else:
            df.insert(0, 'Health', health_col)
            
        return df
    except Exception as e:
        st.error(f"Critical Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    health_counts = df['Health'].value_counts()
    
    c1.metric("Overdue (Red)", health_counts.get("🔴 OVERDUE", 0))
    c2.metric("At Risk (Yellow)", health_counts.get("🟡 AT RISK", 0))
    c3.metric("On Track (Green)", health_counts.get("🟢 Done", 0))
    # Shows average as a whole number (e.g., 0.85 -> 85%)
    c4.metric("Avg. Completion", f"{int(df['Progress %'].mean() * 100)}%")

    # --- TRACKER ---
    st.divider()
    
    # Sidebar Filters
    owners = sorted(df['Owner'].dropna().unique().tolist()) if 'Owner' in df.columns else []
    selected_owner = st.sidebar.multiselect("Filter by Owner", options=owners, default=owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)] if 'Owner' in df.columns else df

    st.data_editor(
        filtered_df,
        num_rows="dynamic",
        column_config={
            "Health": st.column_config.TextColumn("Health", width="small"),
            "Deadline": st.column_config.DateColumn("Deadline", format="YYYY-MM-DD"),
            "Progress %": st.column_config.NumberColumn(
                "Progress (%)",
                help="Enter 1.0 for 100%, 0.5 for 50%",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f" 
            ),
            "Status": st.column_config.SelectboxColumn(
                options=["Not Started", "In Progress", "Completed", "On Hold"]
            ),
        },
        hide_index=True,
        use_container_width=True
    )

    # --- SAVE ---
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Save & Download Updated Tracker", data=csv, file_name='csf_tracker.csv', mime='text/csv')
