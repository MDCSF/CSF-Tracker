import streamlit as st
import pandas as pd
import plotly.express as px

# Load the data
df = pd.read_csv('tracker_data.csv')

st.title("🚀 CSF Team Action Item Tracker")

# Sidebar Filters
owner_filter = st.sidebar.multiselect("Filter by Owner", options=df['Owner'].unique(), default=df['Owner'].unique())
status_filter = st.sidebar.multiselect("Filter by Status", options=df['Status'].unique(), default=df['Status'].unique())

filtered_df = df[(df['Owner'].isin(owner_filter)) & (df['Status'].isin(status_filter))]

# Dashboard Metrics
st.header("📊 Progress Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Tasks", len(filtered_df))
col2.metric("Completed", len(filtered_df[filtered_df['Status'] == 'Completed']))
col3.metric("Avg. Progress (%)", f"{int(filtered_df['Progress %'].mean() * 100)}%")

# Visualizations
fig = px.pie(filtered_df, names='Status', title='Task Distribution', hole=0.4)
st.plotly_chart(fig)

# Interactive Table for Updates
st.header("📝 Task Tracker")
st.write("Team members can view and manage their tasks below:")
edited_df = st.data_editor(filtered_df, num_rows="dynamic")

if st.button("Save Changes"):
    # In a real app, this would save to a database or Google Sheet
    st.success("Progress updated successfully!")
