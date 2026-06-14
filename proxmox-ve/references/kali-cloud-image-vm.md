# Kali Linux Cloud Image VM on Proxmox

Covers provisioning a **Kali Linux** QEMU/KVM VM from the official cloud image, with Hermes Agent installed and full pentesting tool access — matching the "AI agent on Kali" pattern from zSecurity's OpenClaw demo.

## Key Differences from Ubuntu/Debian Cloud Images

| Aspect | Ubuntu/Debian | Kali |
|--------|--------------|------|
| Image format | Direct `.qcow2` download | `.tar.xz` containing `disk.raw` |
| Disk conversion | Skip (already qcow2) | Must convert raw→qcow2 via `qemu-img convert` |
| Default user | `ubuntu` | `root` |
| Python packages | pip works directly | PEP 668 blocks system pip → use pipx |
| Pre-installed tools | Minimal | Full pentesting suite (nmap, msf, hydra, etc.) |

## Step-by-Step

### 1. Download Kali Cloud Image

```bash
# Find the latest version at https://kali.download/cloud-images/current/
# As of 2026, the URL structure is:
curl -sL -o kali-cloud.tar.xz \
  'https://kali.download/cloud-images/current/kali-linux-2026.1-cloud-genericcloud-amd64.tar.xz'

# Extract — contains a single `disk.raw` file (25G sparse, ~845MB real)
tar xf kali-cloud.tar.xz
ls -lh disk.raw
# → disk.raw: DOS/MBR boot sector, 25 GiB
```

### 2. Convert to QCOW2

The raw disk must be converted to qcow2 for Proxmox import:

```bash
qemu-img convert -f raw -O qcow2 disk.raw kali.qcow2
rm disk.raw  # save space
```

### 3. Create the VM

```bash
VMID=106   # use next available from cluster

qm create $VMID \
  --name kali \
  --memory 4096 \
  --cores 4 \
  --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --agent enabled=1 \
  --ostype l26

# Import the converted disk
qm importdisk $VMID kali.qcow2 local-lvm

# Attach as scsi0 and set boot order
qm set $VMID \
  --scsihw virtio-scsi-pci \
  --scsi0 local-lvm:vm-$VMID-disk-0 \
  --boot order=scsi0

# Add cloud-init drive (MUST use local-lvm, NOT local)
qm set $VMID --ide2 local-lvm:cloudinit
```

### 4. Configure Cloud-Init

Kali cloud images default to root login. Inject SSH key from the agent's host:

```bash
qm set $VMID \
  --ciuser root \
  --sshkeys <(echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... user@host') \
  --ipconfig0 ip=dhcp
```

**Pitfall:** The SSH key in `--sshkeys` must be the agent's public key, NOT the Proxmox host's `authorized_keys`. Cloud-init injects the content literally — if the Proxmox host doesn't have the agent's key in its own authorized_keys, the agent can't SSH in.

### 5. Resize Disk and Boot

```bash
qm resize $VMID scsi0 50G   # expand from 25G to 50G
qm start $VMID
```

### 6. Find the IP

```bash
# Method 1: nmap scan by MAC address (get MAC from qm config)
nmap -sn 192.168.1.0/24 | grep -B 2 "$(qm config $VMID | grep net0 | grep -oP 'BC:24:11:[0-9A-F:]+')"

# Method 2: after QEMU guest agent installs
qm guest cmd $VMID network-get-interfaces
```

### 7. Post-Boot Setup

SSH in as root, then:

```bash
# Install QEMU guest agent
apt install -y qemu-guest-agent
systemctl start qemu-guest-agent
# (don't try to enable — the udev hotplug activates it on reboot)

# Create non-root user with sudo access
useradd -m -G sudo -s /bin/bash hermes
echo 'hermes:kali2026!' | chpasswd
mkdir -p /home/hermes/.ssh
cp /root/.ssh/authorized_keys /home/hermes/.ssh/
chown -R hermes:hermes /home/hermes/.ssh
chmod 700 /home/hermes/.ssh
chmod 600 /home/hermes/.ssh/authorized_keys
echo 'hermes ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/hermes
```

### 8. Install Hermes Agent

Kali's Python has PEP 668 protection — use pipx, not pip:

```bash
apt install -y pipx

# Install Hermes Agent
pipx install hermes-agent
# → hermes, hermes-acp, hermes-agent available at ~/.local/bin/

# Add to PATH for all shells
echo 'export PATH=$HOME/.local/bin:$PATH' >> /root/.bashrc
echo 'export PATH=$HOME/.local/bin:$PATH' >> /home/hermes/.bashrc
echo 'export PATH=$HOME/.local/bin:$PATH' >> /home/hermes/.profile

# Symlink globally for non-interactive SSH
ln -sf /root/.local/bin/hermes /usr/local/bin/hermes

# Configure provider (e.g. DeepSeek)
echo 'DEEPSEEK_API_KEY=sk-your-key-here' >> /home/hermes/.hermes/.env
chmod 600 /home/hermes/.hermes/.env
su - hermes -c 'hermes config set model.default deepseek-chat'
su - hermes -c 'hermes config set model.provider deepseek'

# Verify
hermes --version
```

### 9. Verify Tools

Kali cloud images ship with the full pentesting toolchain pre-installed:

```bash
# Check key tools
for tool in nmap msfconsole sqlmap hydra gobuster dirb nikto searchsploit \
            dnsrecon enum4linux netcat socat tcpdump wpscan; do
  which $tool && $tool --version 2>&1 | head -1 || echo "MISSING: $tool"
done
```

Test Hermes can see them:
```bash
hermes chat -q "Run: which nmap msfconsole hydra && nmap --version | head -1" -Q
```

## Pitfalls

1. **Kali cloud image is a `.tar.xz`, not a `.qcow2` directly.** Don't try to import `disk.raw` into Proxmox — it's raw format, not qcow2. Always convert first: `qemu-img convert -f raw -O qcow2 disk.raw kali.qcow2`

2. **PEP 668 blocks pip system install.** Kali uses `--break-system-packages`-resistant packaging. Always use pipx, venv, or the official Hermes install script. `pip install hermes-agent` will fail with a note about using a virtual environment.

3. **SSH to non-root user fails even with key copied.** If SSH to the `hermes` user gets "Permission denied (publickey)" despite the key being in `~hermes/.ssh/authorized_keys`, the issue is usually:
   - The SSH session didn't offer the right key (SSH agent may have multiple keys). Use `-i ~/.ssh/id_ed25519` explicitly.
   - Permissions mismatch on `.ssh/authorized_keys` (must be 600 owned by the user).
   - `sshd` didn't restart after user creation — run `systemctl restart sshd`.

4. **Kali cloud image has no non-root user by default.** The `--ciuser` in cloud-init can create one, but the Kali image only guarantees `root`. Create the `hermes` user manually in post-boot steps.

5. **QEMU guest agent cannot be enabled via systemctl.** The Kali package has no `[Install]` section — the agent activates on udev virtio-serial hotplug. Just `systemctl start` it; it re-activates on reboot automatically.

6. **Kali rolling updates frequently.** After provisioning, run `apt update && apt dist-upgrade -y` to catch any kernel/security updates. Kali 2026.2→2026.3 happens ~quarterly.

## Source URLs

- Kali cloud images index: https://kali.download/cloud-images/current/
- Direct download (2026.1): `https://kali.download/cloud-images/current/kali-linux-2026.1-cloud-genericcloud-amd64.tar.xz`
- Verify: SHA256SUMS in the same directory
