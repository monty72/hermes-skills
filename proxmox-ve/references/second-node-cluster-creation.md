# Second Node Cluster Creation — Session Notes

Date: 2026-05-29
Node 1: "pve1" — 192.168.1.6 — AMD Ryzen 7 5825U, 64GB — PVE 9.2.2
Node 2: "pve2" — 192.168.1.5 — Intel i5-9600T, 31GB — PVE 8.3.0 (upgraded to 9.2.3)

## Discovery & Network

The second node was a bare-metal machine. After power-on, it appeared on 192.168.1.5:
- Port 8006 was open (Proxmox API) but returned 401 without auth
- Port 22 SSH with OpenSSH 9.2p1 (Debian 12)
- Port 111 RPC portmapper

## SSH Key Injection

The Proxmox API `PUT /access/users/root@pam` does NOT accept `ssh-keys` (root is `@pam` realm, not `@pve`). Used sshpass:

```bash
# On the agent host (192.168.1.121)
sudo apt-get install -y sshpass
sshpass -p 'M0nty1979!!' ssh-copy-id -o StrictHostKeyChecking=accept-new root@192.168.1.5
```

## Repo Fix & Initial Update

Fresh PVE 8.3.0 had enterprise repo enabled (401 Unauthorized). Switched to no-subscription:

```bash
ssh root@192.168.1.5 '
  sed -i "s/^deb/#deb/" /etc/apt/sources.list.d/pve-enterprise.list
  echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
    > /etc/apt/sources.list.d/pve-no-subscription.list
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq
'
```

218 packages upgraded on first run. Needed a reboot (new kernel).

## PVE 8→9 Upgrade

Switched repos from bookworm to trixie:

```bash
ssh root@192.168.1.5 '
  cat > /etc/apt/sources.list << EOF
deb http://ftp.uk.debian.org/debian trixie main contrib
deb http://ftp.uk.debian.org/debian trixie-updates main contrib
deb http://security.debian.org trixie-security main contrib
EOF
  sed -i "s/bookworm/trixie/g" /etc/apt/sources.list.d/pve-no-subscription.list
  apt-get update -qq
'
```

Initial `DEBIAN_FRONTEND=noninteractive` run failed on `base-files` conffile for `/etc/issue`. Resolved with `dpkg --configure -a --force-confdef --force-confold`.

Second attempt failed on `lvm2` conffile for `/etc/lvm/lvm.conf`. Resolved with:

```bash
DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confnew" lvm2
```

This freed the chain: libpve-storage-perl → pve-container → qemu-server → pve-manager → proxmox-ve.

Final state: pve-manager/9.2.3, kernel 7.0.2-7-pve.

GRUB fix (prompted but cosmetic — systemd-boot was handling it):

```bash
echo "grub-efi-amd64 grub2/force_efi_extra_removable boolean true" | debconf-set-selections -v -u
apt-get install --reinstall -y grub-efi-amd64
```

## Cluster Creation

### Create cluster on Node 1

```bash
ssh root@192.168.1.6 'pvecm create homelab'
```

### Fix hostname conflict

Both nodes defaulted to `pve`. Renamed Node 2:

```bash
ssh root@192.168.1.5 '
  echo "pve2" > /etc/hostname
  hostname pve2
  echo "192.168.1.5 pve2" >> /etc/hosts
'
```

### Join Node 2

`pvecm add` is interactive (fingerprint + password prompts). Used expect:

```bash
ssh root@192.168.1.5 'apt-get install -y expect -qq'

cat > /tmp/pvecm.exp << 'EXPECT'
#!/usr/bin/expect -f
set timeout 60
spawn pvecm add 192.168.1.6 --force
expect {
    "Are you sure" { send "yes\r"; exp_continue }
    "assword" { send "M0nty1979!!\r"; exp_continue }
    eof { puts "DONE"; exit 0 }
    timeout { puts "TIMEOUT"; exit 1 }
}
EXPECT
chmod +x /tmp/pvecm.exp
/tmp/pvecm.exp
```

Key issues during join:
1. First attempt: stale `/var/lock/pvecm.lock`. Removed with `rm -f`.
2. First attempt: hostname `pve` failed name resolution. Needed `/etc/hosts` entry.
3. `--force` required because Node 2 had existing configured VMs (empty, but PVE detected them).
4. Stopping `pve-cluster` during troubleshooting broke API access (both web UI and SSH key auth). Recovery: used `sshpass` with password to restart `systemctl start pve-cluster`.

Final cluster state:
- 2 nodes (pve1 @ 192.168.1.6, pve2 @ 192.168.1.5)
- Quorate
- PVE 9.2.x on both
