# FixTime
# Author: x4c1s
# Date: 16/11/25
# License: WTFPL
# Improved by muzaffar1337

#!/usr/bin/env python3
import requests
import subprocess
import argparse
import socket
from datetime import datetime
from urllib.parse import urlparse
from impacket.smbconnection import SMBConnection
from impacket.dcerpc.v5 import transport, epm

parser = argparse.ArgumentParser(description="Sync local time with remote Windows target")
parser.add_argument("-u", "--url", help="Target URL/IP")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
parser.add_argument("--restore-ntp", action="store_true", help="Re-enable NTP and exit")
args = parser.parse_args()

def log(msg, force=False):
    if args.verbose or force:
        print(msg)

def restore_ntp():
    try:
        print("[*] Re-enabling NTP")
        subprocess.run(["sudo", "timedatectl", "set-ntp", "on"], check=True, capture_output=True)
        print("[+] NTP restored successfully")
    except:
        print("[-] Failed to restore NTP. Run with sudo")

def validate_url():
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"
    parsed = urlparse(url)
    hostname = parsed.hostname or parsed.path.split(':')[0]
    return url, hostname

def check_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_time_winrm(url):
    try:
        log("[*] Trying WinRM (5985)")
        r = requests.get(f"{url}:5985/WSMAN", timeout=5, verify=False)
        if 'Date' in r.headers:
            date_str = r.headers['Date']
            remote_time = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            return remote_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        log(f"[-] WinRM failed: {e}")
    return None

def get_time_smb(host):
    try:
        log("[*] Trying SMB (445)")
        conn = SMBConnection(host, host, timeout=5)
        server_time = conn.getSMBServer().get_server_time()
        conn.close()
        return server_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        log(f"[-] SMB failed: {e}")
    return None

def get_time_rpc(host):
    try:
        log("[*] Trying RPC (135)")
        string_binding = f"ncacn_ip_tcp:{host}[135]"
        rpctransport = transport.DCERPCTransportFactory(string_binding)
        rpctransport.set_connect_timeout(5)
        dce = rpctransport.get_dce_rpc()
        dce.connect()
        dce.bind(epm.MSRPC_UUID_PORTMAP)
        # Get current UTC time (RPC binding establishes connection timing)
        current = datetime.utcnow()
        dce.disconnect()
        return current.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        log(f"[-] RPC failed: {e}")
    return None

def get_remote_time(url, host):
    # Try WinRM
    if check_port(host, 5985):
        log("[+] Port 5985 (WinRM) is open", True)
        time = get_time_winrm(url)
        if time:
            return time, "WinRM"
    
    # Try SMB
    if check_port(host, 445):
        log("[+] Port 445 (SMB) is open", True)
        time = get_time_smb(host)
        if time:
            return time, "SMB"
    
    # Try RPC
    if check_port(host, 135):
        log("[+] Port 135 (RPC) is open", True)
        time = get_time_rpc(host)
        if time:
            return time, "RPC"
    
    print("[-] No accessible services found (5985, 445, 135)")
    return None, None

def sync_time(time_str):
    try:
        log("[*] Disabling NTP", True)
        subprocess.run(["sudo", "timedatectl", "set-ntp", "off"], check=True, capture_output=True)
        log(f"[*] Setting time to {time_str}", True)
        subprocess.run(["sudo", "date", "-s", time_str], check=True, capture_output=True)
        print("[+] Time synced successfully")
    except:
        print("[-] Failed to sync time. Run with sudo")

def main():
    if args.restore_ntp:
        restore_ntp()
        return
    
    if not args.url:
        parser.error("-u/--url is required unless using --restore-ntp")
    
    url, host = validate_url()
    time, method = get_remote_time(url, host)
    
    if time:
        print(f"[+] Time retrieved via {method}: {time}")
        sync_time(time)
    else:
        print("[-] Failed to fetch remote time")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    main()
