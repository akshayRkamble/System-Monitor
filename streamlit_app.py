import streamlit as st
import psutil
import platform
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import threading
import queue
import os

# Import functions from system_monitor.py
from system_monitor import (
    get_size, get_system_info, get_cpu_info, get_memory_info,
    get_disk_info, get_network_info, get_processes
)

# Initialize session state for storing historical data
if 'cpu_history' not in st.session_state:
    st.session_state.cpu_history = []
if 'memory_history' not in st.session_state:
    st.session_state.memory_history = []
if 'network_history' not in st.session_state:
    st.session_state.network_history = []

def update_metrics():
    """Update metrics in the background"""
    while True:
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent()
            st.session_state.cpu_history.append(cpu_percent)
            if len(st.session_state.cpu_history) > 100:  # Keep last 100 points
                st.session_state.cpu_history.pop(0)

            # Memory Usage
            memory = psutil.virtual_memory()
            st.session_state.memory_history.append(memory.percent)
            if len(st.session_state.memory_history) > 100:
                st.session_state.memory_history.pop(0)

            # Network Usage
            net_io = psutil.net_io_counters()
            st.session_state.network_history.append({
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            })
            if len(st.session_state.network_history) > 100:
                st.session_state.network_history.pop(0)

            time.sleep(1)
        except Exception as e:
            st.error(f"Error updating metrics: {str(e)}")
            time.sleep(5)  # Wait longer on error

def create_cpu_chart():
    """Create CPU usage chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=st.session_state.cpu_history,
        mode='lines',
        name='CPU Usage',
        line=dict(color='#1f77b4')
    ))
    fig.update_layout(
        title='CPU Usage Over Time',
        yaxis_title='Usage (%)',
        yaxis_range=[0, 100],
        height=300,
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_memory_chart():
    """Create memory usage chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=st.session_state.memory_history,
        mode='lines',
        name='Memory Usage',
        line=dict(color='#ff7f0e')
    ))
    fig.update_layout(
        title='Memory Usage Over Time',
        yaxis_title='Usage (%)',
        yaxis_range=[0, 100],
        height=300,
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_network_chart():
    """Create network usage chart"""
    if not st.session_state.network_history:
        return None
    
    df = pd.DataFrame(st.session_state.network_history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=df['bytes_sent'],
        mode='lines',
        name='Bytes Sent',
        line=dict(color='#2ca02c')
    ))
    fig.add_trace(go.Scatter(
        y=df['bytes_recv'],
        mode='lines',
        name='Bytes Received',
        line=dict(color='#d62728')
    ))
    fig.update_layout(
        title='Network Usage Over Time',
        yaxis_title='Bytes',
        height=300,
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def main():
    st.set_page_config(
        page_title="System Monitor",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for light theme
    st.markdown("""
        <style>
        .stApp {
            background-color: #ffffff;
            color: #262730;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stMetric:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        .stHeader {
            color: #262730;
            font-weight: bold;
        }
        .stDataFrame {
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stPlotlyChart {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🖥️ System Monitor Dashboard")

    # Start background thread for metrics
    if 'thread_started' not in st.session_state:
        st.session_state.thread_started = True
        thread = threading.Thread(target=update_metrics, daemon=True)
        thread.start()

    try:
        # System Information
        st.header("System Information")
        system_info = get_system_info()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("System", system_info["System"])
            st.metric("Node Name", system_info["Node Name"])
            st.metric("Release", system_info["Release"])
        with col2:
            st.metric("Machine", system_info["Machine"])
            st.metric("Processor", system_info["Processor"])
            st.metric("Version", system_info["Version"])

        # CPU Information
        st.header("CPU Information")
        cpu_info = get_cpu_info()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Physical Cores", cpu_info["Physical cores"])
            st.metric("Total Cores", cpu_info["Total cores"])
        with col2:
            st.metric("Max Frequency", cpu_info["Max Frequency"])
            st.metric("Current Frequency", cpu_info["Current Frequency"])
        with col3:
            st.metric("CPU Usage", cpu_info["CPU Usage"])
        
        # CPU Usage Chart
        st.plotly_chart(create_cpu_chart(), use_container_width=True)

        # Memory Information
        st.header("Memory Information")
        memory_info = get_memory_info()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Memory", memory_info["Total"])
        with col2:
            st.metric("Available Memory", memory_info["Available"])
        with col3:
            st.metric("Used Memory", memory_info["Used"])
        with col4:
            st.metric("Memory Usage", memory_info["Percentage"])
        
        # Memory Usage Chart
        st.plotly_chart(create_memory_chart(), use_container_width=True)

        # Disk Information
        st.header("Disk Information")
        disk_info = get_disk_info()
        df_disk = pd.DataFrame(disk_info)
        st.dataframe(
            df_disk,
            column_config={
                "Device": st.column_config.TextColumn("Device"),
                "Mountpoint": st.column_config.TextColumn("Mountpoint"),
                "File system type": st.column_config.TextColumn("File System"),
                "Total Size": st.column_config.TextColumn("Total Size"),
                "Used": st.column_config.TextColumn("Used"),
                "Free": st.column_config.TextColumn("Free"),
                "Percentage": st.column_config.TextColumn("Usage %")
            },
            hide_index=True
        )

        # Network Information
        st.header("Network Information")
        network_info = get_network_info()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Bytes Sent", network_info["Bytes sent"])
        with col2:
            st.metric("Bytes Received", network_info["Bytes received"])
        with col3:
            st.metric("Packets Sent", network_info["Packets sent"])
        with col4:
            st.metric("Packets Received", network_info["Packets received"])
        
        # Network Usage Chart
        network_chart = create_network_chart()
        if network_chart:
            st.plotly_chart(network_chart, use_container_width=True)

        # Process Information
        st.header("Process Information")
        processes = get_processes()
        df_processes = pd.DataFrame(processes)
        st.dataframe(
            df_processes,
            column_config={
                "pid": st.column_config.NumberColumn("PID"),
                "name": st.column_config.TextColumn("Name"),
                "username": st.column_config.TextColumn("Username"),
                "memory_percent": st.column_config.NumberColumn("Memory %", format="%.1f%%"),
                "cpu_percent": st.column_config.NumberColumn("CPU %", format="%.1f%%")
            },
            hide_index=True
        )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Some features might not be available in the cloud environment.")

if __name__ == "__main__":
    main() 