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
import sys
import random

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

# Determine if running in cloud environment
def is_cloud_environment():
    """Check if we're running in Streamlit cloud"""
    return 'STREAMLIT_SHARING' in os.environ or 'STREAMLIT_CLOUD' in os.environ

# For demo mode, we'll simulate Windows system information
DEMO_SYSTEM_INFO = {
    "System": "Windows",
    "Node Name": "DESKTOP-WIN10PRO",
    "Release": "10",
    "Version": "10.0.19045",
    "Machine": "AMD64",
    "Processor": "Intel64 Family 6 Model 142 Stepping 12, GenuineIntel"
}

DEMO_CPU_INFO = {
    "Physical cores": "4",
    "Total cores": "8",
    "Max Frequency": "3.60Mhz",
    "Current Frequency": "2.80Mhz",
    "CPU Usage": "25%"
}

def safe_cpu_percent():
    """Get CPU usage safely"""
    try:
        return psutil.cpu_percent(interval=0.1)
    except Exception:
        # Return random data for demo purposes in cloud
        last = 25 if not st.session_state.cpu_history else st.session_state.cpu_history[-1]
        return max(min(last + random.uniform(-5, 5), 100), 0)

def safe_memory_info():
    """Get memory info safely"""
    try:
        return psutil.virtual_memory()
    except Exception:
        # Return stable data for demo purposes
        class DummyMemory:
            def __init__(self):
                last = 65 if not st.session_state.memory_history else st.session_state.memory_history[-1]
                self.percent = max(min(last + random.uniform(-3, 3), 100), 0)
                self.total = 16 * 1024 * 1024 * 1024  # 16GB - more typical for Windows
                self.available = self.total * (1 - self.percent/100)
                self.used = self.total - self.available
        return DummyMemory()

def safe_network_info():
    """Get network info safely"""
    try:
        return psutil.net_io_counters()
    except Exception:
        # Return increasing data for demo purposes
        class DummyNetwork:
            def __init__(self):
                self.last_sent = st.session_state.get('last_bytes_sent', 1000000)
                self.last_recv = st.session_state.get('last_bytes_recv', 5000000)
                
                # Increment slightly each time with some randomness
                self.bytes_sent = self.last_sent + random.randint(5000, 15000)
                self.bytes_recv = self.last_recv + random.randint(10000, 30000)
                self.packets_sent = random.randint(900, 1100)
                self.packets_recv = random.randint(1800, 2200)
                
                # Save for next time
                st.session_state['last_bytes_sent'] = self.bytes_sent
                st.session_state['last_bytes_recv'] = self.bytes_recv
        return DummyNetwork()

def update_metrics():
    """Update metrics in the background"""
    while True:
        try:
            # CPU Usage
            cpu_percent = safe_cpu_percent()
            st.session_state.cpu_history.append(cpu_percent)
            if len(st.session_state.cpu_history) > 100:  # Keep last 100 points
                st.session_state.cpu_history.pop(0)

            # Memory Usage
            memory = safe_memory_info()
            st.session_state.memory_history.append(memory.percent)
            if len(st.session_state.memory_history) > 100:
                st.session_state.memory_history.pop(0)

            # Network Usage
            net_io = safe_network_info()
            st.session_state.network_history.append({
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            })
            if len(st.session_state.network_history) > 100:
                st.session_state.network_history.pop(0)

            time.sleep(1)
        except Exception as e:
            print(f"Error updating metrics: {str(e)}", file=sys.stderr)
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

def safe_get_system_info():
    """Get system info safely"""
    try:
        # First try to get real system info
        return get_system_info()
    except Exception:
        # On failure, return Windows-like demo data
        return DEMO_SYSTEM_INFO

def safe_get_cpu_info():
    """Get CPU info safely"""
    try:
        # First try to get real CPU info
        return get_cpu_info()
    except Exception:
        # On failure, get Windows-like CPU info with current CPU usage
        info = DEMO_CPU_INFO.copy()
        info["CPU Usage"] = f"{safe_cpu_percent():.1f}%"
        return info

def safe_get_memory_info():
    """Get memory info safely"""
    try:
        return get_memory_info()
    except Exception:
        memory = safe_memory_info()
        return {
            "Total": get_size(memory.total),
            "Available": get_size(memory.available),
            "Used": get_size(memory.used),
            "Percentage": f"{memory.percent:.1f}%"
        }

def safe_get_disk_info():
    """Get disk info safely"""
    try:
        return get_disk_info()
    except Exception:
        # Return Windows-like dummy disk data
        return [
            {
                "Device": "C:\\",
                "Mountpoint": "C:\\",
                "File system type": "NTFS",
                "Total Size": "237.86GB",
                "Used": "67.23GB",
                "Free": "170.63GB",
                "Percentage": "28.3%"
            },
            {
                "Device": "D:\\",
                "Mountpoint": "D:\\",
                "File system type": "NTFS",
                "Total Size": "321.75GB",
                "Used": "3.16GB",
                "Free": "318.59GB",
                "Percentage": "1.0%"
            }
        ]

def safe_get_network_info():
    """Get network info safely"""
    try:
        return get_network_info()
    except Exception:
        net_io = safe_network_info()
        return {
            "Bytes sent": get_size(net_io.bytes_sent),
            "Bytes received": get_size(net_io.bytes_recv),
            "Packets sent": net_io.packets_sent,
            "Packets received": net_io.packets_recv
        }

def safe_get_processes():
    """Get processes safely"""
    try:
        return get_processes()
    except Exception:
        # Return Windows-like dummy processes
        return [
            {"pid": 4, "name": "System", "username": "SYSTEM", "memory_percent": 0.1, "cpu_percent": 0.1},
            {"pid": 504, "name": "svchost.exe", "username": "SYSTEM", "memory_percent": 1.5, "cpu_percent": 0.5},
            {"pid": 812, "name": "explorer.exe", "username": "USER", "memory_percent": 3.0, "cpu_percent": 1.0},
            {"pid": 1012, "name": "chrome.exe", "username": "USER", "memory_percent": 5.0, "cpu_percent": 4.0},
            {"pid": 1230, "name": "StreamlitApp.exe", "username": "USER", "memory_percent": 2.5, "cpu_percent": 3.0}
        ]

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

    # Check if we're in cloud environment
    cloud_mode = is_cloud_environment()
    if cloud_mode:
        st.info("⚠️ Running in demo mode - Windows system metrics are simulated for demonstration purposes.")

    # Start background thread for metrics
    if 'thread_started' not in st.session_state:
        st.session_state.thread_started = True
        thread = threading.Thread(target=update_metrics, daemon=True)
        thread.start()

    try:
        # System Information
        st.header("System Information")
        system_info = safe_get_system_info()
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
        cpu_info = safe_get_cpu_info()
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
        memory_info = safe_get_memory_info()
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
        disk_info = safe_get_disk_info()
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
        network_info = safe_get_network_info()
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
        processes = safe_get_processes()
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