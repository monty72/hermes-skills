# Cloud-Image VM Workflow — Session Walkthrough

This is a full annotated transcript of creating an Ubuntu 24.04 LTS VM from a cloud image on Proxmox VE 9.2.2, including error recovery steps.

## Context

- Proxmox host: pve1 (192.168.1.6), Proxmox VE 9.2.2, running kernel 7.0.2-6-pve
- Hermes agent: VM 105 on the same Proxmox host
- Target VM: ID 104, named `opencrawl`, 8 vCPU, 16GB RAM, 50GB disk
- SSH access to Proxmox via `~/.ssh/proxmox` key, configured as Host `proxmox-backup` in `~/.ssh/config`

## Step 1 — Check Available ISOs and Images

```bash
ssh proxmox-backup "ls -lh /var/lib/vz/template/iso/ 2>/dev/null"
```

Ubuntu Server ISO wasn't cached. Ubuntu Desktop ISO (6.2GB) was, but the server cloud image is only ~600MB and preferred.

## Step 2 — Download Cloud Image

```bash
# Find the latest Ubuntu 24.04 cloud image
# The canonical URL:
#   https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img

# Download it to a known location:
ssh proxmox-backup "mkdir -p /var/lib/vz/template/qemu && cd /var/lib/vz/template/qemu && \
  wget 'https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img' \
  -O ubuntu-24.04-server-cloudimg-amd64.img"
```

**Error encountered:** The `mkdir -p` and `cd` ran in the same shell block but `cd` failed silently because the SSH command groups multiple statements. The file was written to `/root/` instead of `/var/lib/vz/template/qemu/`. Always verify the file location after download:

```bash
ls -lh /root/ubuntu-24.04-server-cloudimg-amd64.img
# If there, move it to the right place:
mv /root/ubuntu-24.04-server-cloudimg-amd64.img /var/lib/vz/template/qemu/
```

The file is ~599MB QCOW2. Verify with `file`:
```
QEMU QCOW Image (v3), 3758096384 bytes
```

## Step 3 — Create VM Skeleton

```bash
# Create VM 104 with specs
qm create 104 \
  --name opencrawl \
  --memory 16384 \
  --cores 8 \
  --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --agent enabled=1 \
  --ostype l26
```

## Step 4 — Import and Attach Disk

```bash
# Import cloud image into local-lvm
qm importdisk 104 /root/ubuntu-24.04-server-cloudimg-amd64.img local-lvm

# Set as scsi0 boot disk
qm set 104 \
  --scsihw virtio-scsi-pci \
  --scsi0 local-lvm:vm-104-disk-0 \
  --boot order=scsi0
```

The import expands the QCOW2 to a 3.5GB LVM volume on local-lvm.

## Step 5 — Add Cloud-Init Drive

```bash
# WRONG — this fails on start:
qm set 104 --ide2 local:cloudinit
# "storage 'local' does not support content-type 'images'"

# CORRECT — use local-lvm:
qm set 104 --delete ide2           # remove the broken one
qm set 104 --ide2 local-lvm:cloudinit
```

**Root cause:** The `local` storage (directory-based at `/var/lib/vz/`) supports `iso`, `vztmpl`, and `backup` content types but NOT `images`. `local-lvm` (LVM thin pool) supports `rootdir` and `images`. The cloud-init ISO is technically an image, so it needs to go on `local-lvm`.

## Step 6 — Configure Cloud-Init (CRITICAL)

```bash
# The agent's public key (NOT the Proxmox host's key):
AGENT_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIxnOnPA7iKoh34nhvD0O6mUdk3YxY6KZ53es2qzn1XL matth@Hermes"

qm set 104 \
  --ciuser matth \
  --sshkeys <(echo "$AGENT_KEY") \
  --ipconfig0 ip=dhcp
```

**Critical pitfall:** `--sshkey /root/.ssh/authorized_keys` injects the **Proxmox host's** authorized_keys file. If the agent's key is only on the agent VM and not in the Proxmox host's authorized_keys, SSH into the fresh VM will fail with `Permission denied (publickey)`.

Always pass the agent's public key explicitly via process substitution `--sshkeys <(echo 'ssh-ed25519 AAAA...')`.

## Step 7 — Resize and Boot

```bash
qm resize 104 scsi0 50G
qm start 104
```

## Step 8 — Find the IP Address

```bash
# Use nmap to find the VM by MAC (from qm config output):
# scsi0: local-lvm:vm-104-disk-0,size=50G
# Check the net0 line in qm config for the MAC: BC:24:11:C9:90:5B
nmap -sn 192.168.1.0/24 | grep -B 2 'BC:24:11:C9:90:5B'
# Returns: Nmap scan report for ubuntu.lan (192.168.1.137)
```

The MAC is visible in `qm config 104` output:
```
net0: virtio=BC:24:11:C9:90:5B,bridge=vmbr0
```

## Step 9 — SSH and Install Guest Agent

```bash
# Remove old host key from known_hosts (VM was rebuilt)
ssh-keygen -f ~/.ssh/known_hosts -R 192.168.1.137

# SSH in (using agent's key, user matth)
ssh -o StrictHostKeyChecking=accept-new matth@192.168.1.137

# Install qemu-guest-agent
sudo apt-get update
sudo apt-get install -y qemu-guest-agent
sudo systemctl start qemu-guest-agent

# Verify
systemctl is-active qemu-guest-agent  # → active
```

**Note:** `systemctl enable qemu-guest-agent` fails with:
```
The unit files have no installation config (WantedBy=, RequiredBy=, ...)
```
This is normal — the qemu-guest-agent package uses udev/hotplug activation. Don't fight it. Just `start` and it re-activates on reboot.

## Step 10 — Verify with Proxmox

```bash
# Once guest agent is running:
qm guest exec 104 -- hostname
# → {"out-data": "opencrawl\n", "exitcode": 0}

qm guest exec 104 -- cat /etc/os-release
# → PRETTY_NAME="Ubuntu 24.04.4 LTS"
```

## Final State

| Property | Value |
|----------|-------|
| VM ID | 104 |
| Name | opencrawl |
| OS | Ubuntu 24.04.4 LTS |
| Kernel | 6.8.0-117-generic |
| IP | 192.168.1.137/24 (DHCP) |
| vCPU | 8 (host passthrough) |
| RAM | 16 GB |
| Disk | 50 GB (2 GB used, 46 GB free) |
| Guest Agent | Running |
| SSH | Key-based as matth@192.168.1.137 |
