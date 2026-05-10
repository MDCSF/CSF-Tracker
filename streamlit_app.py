import streamlit as st
import pandas as pd

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # skiprows=1 skips the title header in your file
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df.columns = df.columns.str.strip()
        
        # Ensure Progress is a number. If it's 1, it stays 1. If it's 0.75, it stays 0.75.
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0)
        
        # Standardize Dates
        if 'Deadline' in df.columns:
            df['Deadline'] = pd.to_datetime(df['Deadline'], errors='coerce').dt.date
            
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- 1. DASHBOARD SECTION ---
    st.subheader("📊 Status Overview")
    
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Actions", len(df))
        c2.metric("Completed", status_counts.get('Completed', 0))
        c3.metric("In Progress", status_counts.get('In Progress', 0))
        
        # Calculate avg progress as a percentage (e.g., 0.8 -> 80%)
        avg_val = df['Progress %'].mean()
        c4.metric("Avg. Completion", f"{int(avg_val * 100)}%")

        # Native Streamlit Chart (Doesn't require Plotly)
        st.bar_chart(status_counts)

    # --- 2. TRACKER SECTION ---
    st.divider()
    
    # Sidebar Filters
    current_owners = sorted(df['Owner'].dropna().unique().tolist())
    st.sidebar.header("Filter Settings")
    selected_owner = st.sidebar.multiselect("Select Owner", options=current_owners, default=current_owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)]

    st.subheader("📝 Live Action Items")
    st.caption("Instructions: 1.0 = 100%, 0.5 = 50%. Scroll down to '+' to add new items.")

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
            "Status": st.column_config.SelectboxColumn(
                options=["Not Started", "In Progress", "Completed", "On Hold"]
            ),
            "Priority": st.column_config.SelectboxColumn(
                options=["Low", "Medium", "High"]
            ),
            "Owner": st.column_config.TextColumn("Owner")
        },
        hide_index=True,
        use_container_width=True
    )

    # --- 3. SAVE / DOWNLOAD ---
    st.divider()
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Updated Tracker",
        data=csv,
        file_name='csf_tracker_final.csv',
        mime='text/csv'
    )
