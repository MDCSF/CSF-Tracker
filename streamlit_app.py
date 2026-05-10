import streamlit as st
import pandas as pd

st.set_page_config(page_title="CSF Action Tracker", layout="wide")

@st.cache_data
def load_data():
    try:
        # skiprows=1 skips the title row in your CSV
        df = pd.read_csv('tracker_data.csv', skiprows=1)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        df.columns = df.columns.str.strip()
        # Ensure Progress is a decimal between 0 and 1
        df['Progress %'] = pd.to_numeric(df['Progress %'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚀 CSF Team Action Tracker")
    
    # Get a clean list of current owners for the dropdown
    current_owners = sorted(df['Owner'].dropna().unique().tolist())

    # Sidebar Filter
    st.sidebar.header("Filter View")
    selected_owner = st.sidebar.multiselect("Filter by Owner", options=current_owners, default=current_owners)
    
    filtered_df = df[df['Owner'].isin(selected_owner)]

    # The Interactive Tracker
    st.subheader("📝 Action Items")
    st.info("💡 To add a new item: Scroll to the bottom of the table and click the '+' icon.")

    # dynamic num_rows allows the team to add and delete items
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic", 
        column_config={
            "Owner": st.column_config.SelectboxColumn(
                "Owner",
                options=current_owners, # Dropdown for existing team members
                help="Select the person responsible"
            ),
            "Progress %": st.column_config.NumberColumn(
                "Progress (0-1)",
                help="Use 1.0 for 100%, 0.5 for 50%, etc.",
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
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # Save/Download Section
    st.divider()
    st.subheader("💾 Save Progress")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Updated Tracker",
        data=csv,
        file_name='csf_tracker_updated.csv',
        mime='text/csv',
        help="Click here to save the new items and progress updates."
    )
