import subprocess
import sys
import os

# --- SAFETY CATCH: Force install Plotly if missing ---
try:
    import plotly.express as px
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    import plotly.express as px

import streamlit as st
import pandas as pd

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load data skipping the title header
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df.columns = df.columns.str.strip()
        
        # FIX PROGRESS: Convert decimals to percentages and handle errors
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0)
        
        # FIX DATES: Standardize format
        if 'Deadline' in df.columns:
            df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- DASHBOARD ---
    st.subheader("📊 Team Performance Dashboard")
    
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Total Action Items", len(df))
            avg_p = int(df['Progress %'].mean() * 100)
            st.metric("Avg. Completion", f"{avg_p}%")
            
            # Professional Pie Chart
            fig = px.pie(status_counts, values='Count', names='Status', 
                         hole=0.4, color='Status',
                         color_discrete_map={'Completed':'#2ecc71', 'In Progress':'#f1c40f', 'Not Started':'#e74c3c'})
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("### Tasks by Status")
            st.bar_chart(df['Status'].value_counts())

    # --- TRACKER ---
    st.divider()
    
    # Dynamic Owners
    current_owners = sorted(df['Owner'].dropna().unique().tolist())
    st.sidebar.header("Filter View")
    selected_owner = st.sidebar.multiselect("Owner", options=current_owners, default=current_owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)]

    st.subheader("📝 Live Tracker")
    st.caption("Instructions: 1.0 = 100%, 0.5 = 50%. Use the '+' at the bottom to add rows.")

    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        column_config={
            "Deadline": st.column_config.DateColumn("Deadline", format="DD/MM/YYYY"),
            "Progress %": st.column_config.NumberColumn(
                "Progress (%)",
                help="Enter 1.0 for 100%, 0.5 for 50%",
                min_value=0,
                max_value=1,
                step=0.01,
                format="%.2f"
            ),
            "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"]),
            "Priority": st.column_config.SelectboxColumn(options=["Low", "Medium", "High"]),
            "Owner": st.column_config.TextColumn("Owner") 
        },
        hide_index=True,
        use_container_width=True
    )

    # --- DOWNLOAD ---
    st.divider()
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Updated CSV", data=csv, file_name='csf_tracker_updated.csv', mime='text/csv')
