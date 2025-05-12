#!/usr/bin/env python3

import psutil
import platform
import time
from datetime import datetime
import json
import csv
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import click

console = Console()

def get_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

def get_system_info():
    """Get basic system information"""
    uname = platform.uname()
    return {
        "System": uname.system,
        "Node Name": uname.node,
        "Release": uname.release,
        "Version": uname.version,
        "Machine": uname.machine,
        "Processor": uname.processor
    }

def get_cpu_info():
    """Get CPU information"""
    return {
        "Physical cores": psutil.cpu_count(logical=False),
        "Total cores": psutil.cpu_count(logical=True),
        "Max Frequency": f"{psutil.cpu_freq().max:.2f}Mhz" if psutil.cpu_freq() else "N/A",
        "Current Frequency": f"{psutil.cpu_freq().current:.2f}Mhz" if psutil.cpu_freq() else "N/A",
        "CPU Usage": f"{psutil.cpu_percent()}%"
    }

def get_memory_info():
    """Get memory information"""
    svmem = psutil.virtual_memory()
    return {
        "Total": get_size(svmem.total),
        "Available": get_size(svmem.available),
        "Used": get_size(svmem.used),
        "Percentage": f"{svmem.percent}%"
    }

def get_disk_info():
    """Get disk information"""
    partitions = psutil.disk_partitions()
    disk_info = []
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "Device": partition.device,
                "Mountpoint": partition.mountpoint,
                "File system type": partition.fstype,
                "Total Size": get_size(partition_usage.total),
                "Used": get_size(partition_usage.used),
                "Free": get_size(partition_usage.free),
                "Percentage": f"{partition_usage.percent}%"
            })
        except PermissionError:
            continue
    return disk_info

def get_network_info():
    """Get network information"""
    net_io = psutil.net_io_counters()
    return {
        "Bytes sent": get_size(net_io.bytes_sent),
        "Bytes received": get_size(net_io.bytes_recv),
        "Packets sent": net_io.packets_sent,
        "Packets received": net_io.packets_recv
    }

def get_processes():
    """Get list of processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
        try:
            pinfo = proc.info
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)

def display_system_info():
    """Display system information in a table"""
    system_info = get_system_info()
    table = Table(title="System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in system_info.items():
        table.add_row(key, str(value))
    
    console.print(table)

def display_cpu_info():
    """Display CPU information in a table"""
    cpu_info = get_cpu_info()
    table = Table(title="CPU Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in cpu_info.items():
        table.add_row(key, str(value))
    
    console.print(table)

def display_memory_info():
    """Display memory information in a table"""
    memory_info = get_memory_info()
    table = Table(title="Memory Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in memory_info.items():
        table.add_row(key, str(value))
    
    console.print(table)

def display_disk_info():
    """Display disk information in a table"""
    disk_info = get_disk_info()
    table = Table(title="Disk Information")
    table.add_column("Device", style="cyan")
    table.add_column("Mountpoint", style="green")
    table.add_column("File System", style="blue")
    table.add_column("Total Size", style="yellow")
    table.add_column("Used", style="red")
    table.add_column("Free", style="green")
    table.add_column("Percentage", style="magenta")
    
    for disk in disk_info:
        table.add_row(
            disk["Device"],
            disk["Mountpoint"],
            disk["File system type"],
            disk["Total Size"],
            disk["Used"],
            disk["Free"],
            disk["Percentage"]
        )
    
    console.print(table)

def display_network_info():
    """Display network information in a table"""
    network_info = get_network_info()
    table = Table(title="Network Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in network_info.items():
        table.add_row(key, str(value))
    
    console.print(table)

def display_processes():
    """Display process information in a table"""
    processes = get_processes()
    table = Table(title="Process Information")
    table.add_column("PID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Username", style="blue")
    table.add_column("Memory %", style="yellow")
    table.add_column("CPU %", style="red")
    
    for proc in processes[:10]:  # Show top 10 processes
        table.add_row(
            str(proc['pid']),
            proc['name'],
            proc['username'] or "N/A",
            f"{proc['memory_percent']:.1f}%",
            f"{proc['cpu_percent']:.1f}%"
        )
    
    console.print(table)

def export_to_json(filename):
    """Export system information to JSON file"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "system_info": get_system_info(),
        "cpu_info": get_cpu_info(),
        "memory_info": get_memory_info(),
        "disk_info": get_disk_info(),
        "network_info": get_network_info(),
        "processes": get_processes()
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    console.print(f"[green]Data exported to {filename}")

def export_to_csv(filename):
    """Export system information to CSV file"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Metric", "Value"])
        
        timestamp = datetime.now().isoformat()
        
        # System Info
        for key, value in get_system_info().items():
            writer.writerow([timestamp, f"System_{key}", value])
        
        # CPU Info
        for key, value in get_cpu_info().items():
            writer.writerow([timestamp, f"CPU_{key}", value])
        
        # Memory Info
        for key, value in get_memory_info().items():
            writer.writerow([timestamp, f"Memory_{key}", value])
        
        # Network Info
        for key, value in get_network_info().items():
            writer.writerow([timestamp, f"Network_{key}", value])
    
    console.print(f"[green]Data exported to {filename}")

@click.group()
def cli():
    """System Monitor and Process Manager"""
    pass

@cli.command()
def monitor():
    """Display real-time system monitoring"""
    try:
        with Live(auto_refresh=False) as live:
            while True:
                console.clear()
                display_system_info()
                display_cpu_info()
                display_memory_info()
                display_disk_info()
                display_network_info()
                display_processes()
                live.refresh()
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped")

@cli.command()
@click.option('--format', type=click.Choice(['json', 'csv']), default='json', help='Export format')
@click.option('--output', default='system_info', help='Output filename (without extension)')
def export(format, output):
    """Export system information to file"""
    if format == 'json':
        export_to_json(f"{output}.json")
    else:
        export_to_csv(f"{output}.csv")

@cli.command()
def processes():
    """Display process information"""
    display_processes()

if __name__ == '__main__':
    cli() 