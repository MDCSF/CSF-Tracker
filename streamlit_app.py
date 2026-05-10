import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="CSF Action Tracker", layout="wide")

# Load the data
@st.cache_data
def load_data():
    try:
        # Assumes your file is named tracker_data.csv in GitHub
        df = pd.read_csv('tracker_data.csv')
        return df
    except Exception as e:
        st.error(f"Error loading tracker_data.csv: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 Centre for Space Futures: Action Tracker")
    
    # Simple Dashboard using built-in Streamlit tools (No Plotly needed)
    st.subheader("📊 Team Progress Overview")
    
    status_counts = df['Status'].value_counts()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", len(df))
    col2.metric("Completed", status_counts.get('Completed', 0))
    col3.metric("In Progress", status_counts.get('In Progress', 0))

    # Built-in Bar Chart (Works 100% of the time)
    st.bar_chart(status_counts)

    # Sidebar Filter
    st.sidebar.header("Filter")
    owners = sorted(df['Owner'].unique())
    selected_owner = st.sidebar.multiselect("Select Team Member", options=owners, default=owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)]

    # The Interactive Table
    st.subheader("📝 Live Action Item List")
    st.info("Edit your 'Status' or 'Progress %' directly in the table.")
    
    st.data_editor(
        filtered_df,
        column_config={
            "Progress %": st.column_config.NumberColumn(format="%.2f"),
            "Status": st.column_config.SelectboxColumn(options=["Not Started", "In Progress", "Completed", "On Hold"])
        },
        hide_index=True,
        use_container_width=True
    )
