import streamlit as st
import pandas as pd

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load data skipping the title row
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df.columns = df.columns.str.strip()
        
        # FIX: Ensure Progress % is treated as a percentage (0.0 to 100.0)
        # We convert the fraction (like 0.75) to a whole number (75) for display
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # --- 1. DASHBOARD SECTION ---
    st.subheader("📊 Status Overview")
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts()
        
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tasks", len(df))
        m2.metric("Completed", status_counts.get('Completed', 0))
        m3.metric("In Progress", status_counts.get('In Progress', 0))
        
        # Calculate Average Progress
        avg_p = df['Progress %'].mean() 
        # Display as a whole number percentage
        m4.metric("Avg. Progress", f"{int(avg_p * 100)}%")

        # Pie Chart (Using Streamlit's built-in chart for stability)
        st.write("### Task Distribution")
        st.bar_chart(status_counts)

    # --- 2. INTERACTIVE TRACKER ---
    st.divider()
    st.subheader("📝 Action Items")
    
    # Get owners for the dropdown and sidebar
    current_owners = sorted(df['Owner'].dropna().unique().tolist())
    
    # Sidebar for filtering
    st.sidebar.header("Filter View")
    selected_owner = st.sidebar.multiselect("Filter by Owner", options=current_owners, default=current_owners)
    filtered_df = df[df['Owner'].isin(selected_owner)]

    # The Data Editor
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        column_config={
            "Owner": st.column_config.SelectboxColumn(
                "Owner",
                options=current_owners,
                help="Assign an owner to this task"
            ),
            "Progress %": st.column_config.NumberColumn(
                "Progress (%)",
                help="Enter as a decimal (0.5 = 50%, 1.0 = 100%)",
                min_value=0.0,
                max_value=1.0,
                format="%.2f", # This shows 0.75
                step=0.01,
            ),
            "Status": st.column_config.SelectboxColumn(
                options=["Not Started", "In Progress", "Completed", "On Hold"]
            ),
            "Priority": st.column_config.SelectboxColumn(
                options=["Low", "Medium", "High"]
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # --- 3. SAVE / DOWNLOAD ---
    st.divider()
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Updated Tracker",
        data=csv,
        file_name='csf_tracker_updated.csv',
        mime='text/csv'
    )
