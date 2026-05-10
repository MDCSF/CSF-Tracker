import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="CSF Action Tracker", layout="wide")

# Load the data
@st.cache_data
def load_data():
    try:
        # We skip the first row because your file has a title header 
        # before the actual column names.
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        
        # This removes any completely empty rows or columns that might be at the end
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        # Clean up column names in case there are hidden spaces
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        st.error(f"Error reading tracker_data.csv: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 Centre for Space Futures: Action Tracker")
    
    # Check if the column actually exists to prevent the crash
    if 'Status' in df.columns:
        st.subheader("📊 Team Progress Overview")
        status_counts = df['Status'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", len(df))
        col2.metric("Completed", status_counts.get('Completed', 0))
        col3.metric("In Progress", status_counts.get('In Progress', 0))

        st.bar_chart(status_counts)
    else:
        st.warning(f"Column 'Status' not found. Available columns: {', '.join(df.columns)}")

    # Sidebar Filter
    st.sidebar.header("Filter")
    if 'Owner' in df.columns:
        owners = sorted(df['Owner'].dropna().unique())
        selected_owner = st.sidebar.multiselect("Select Team Member", options=owners, default=owners)
        filtered_df = df[df['Owner'].isin(selected_owner)]
    else:
        filtered_df = df

    # The Interactive Table
    st.subheader("📝 Live Action Item List")
    st.info("Edit your progress directly in the table below.")
    
    st.data_editor(
        filtered_df,
        column_config={
            "Progress %": st.column_config.NumberColumn(format="%.2f"),
            "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"])
        },
        hide_index=True,
        use_container_width=True
    )
