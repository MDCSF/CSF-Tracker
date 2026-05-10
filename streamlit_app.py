import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load data skipping the title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df.columns = df.columns.str.strip()
        
        # 1. CLEAN PROGRESS: Force it to be a Float (decimal) right away
        if 'Progress %' in df.columns:
            # Remove any special characters and convert to float
            df['Progress %'] = df['Progress %'].astype(str).str.replace('%', '').str.strip()
            df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0.0)
            
            # If values are whole numbers (75), convert to decimals (0.75)
            # This logic only triggers if the max value is > 1.0
            if df['Progress %'].max() > 1.0:
                df['Progress %'] = df['Progress %'] / 100.0
        
        # 2. CLEAN DEADLINES
        if 'Deadline' in df.columns:
            df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
        
        # 3. APPLY HEALTH LOGIC
        def get_health(row):
            today = date.today()
            deadline = row.get('Deadline')
            progress = float(row.get('Progress %', 0.0))
            status = str(row.get('Status', '')).strip()
            
            if status == 'Completed' or progress >= 1.0:
                return "🟢 Done"
            if pd.notnull(deadline) and deadline < today and progress < 1.0:
                return "🔴 OVERDUE"
            if pd.notnull(deadline) and (deadline - today).days <= 7 and progress < 0.5:
                return "🟡 AT RISK"
            return "⚪ Pending"

        # Force Health column to be a standard string/object type
        df.insert(0, 'Health Status', df.apply(get_health, axis=1).astype(str))
            
        return df
    except Exception as e:
        # If it crashes, show the specific row/error to help us debug
        st.error(f"Critical Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- DASHBOARD ---
    # We calculate counts using the new column name
    health_counts = df['Health Status'].value_counts()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overdue (Red)", health_counts.get("🔴 OVERDUE", 0))
    c2.metric("At Risk (Yellow)", health_counts.get("🟡 AT RISK", 0))
    c3.metric("On Track (Green)", health_counts.get("🟢 Done", 0))
    
    # Display avg progress as a percentage
    avg_p = float(df['Progress %'].mean())
    c4.metric("Avg. Completion", f"{int(avg_p * 100)}%")

    # --- TRACKER ---
    st.divider()
    
    # Sidebar Filters
    if 'Owner' in df.columns:
        owners = sorted(df['Owner'].dropna().unique().tolist())
        selected_owner = st.sidebar.multiselect("Filter by Owner", options=owners, default=owners)
        filtered_df = df[df['Owner'].isin(selected_owner)]
    else:
        filtered_df = df

    # Final Table Configuration
    st.data_editor(
        filtered_df,
        num_rows="dynamic",
        column_config={
            "Health Status": st.column_config.TextColumn("Health", width="small"),
            "Deadline": st.column_config.DateColumn("Deadline", format="YYYY-MM-DD"),
            "Progress %": st.column_config.NumberColumn(
                "Progress (%)",
                help="1.0 = 100%, 0.5 = 50%",
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
    csv_out = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Updated Tracker", data=csv_out, file_name='csf_tracker.csv', mime='text/csv')
