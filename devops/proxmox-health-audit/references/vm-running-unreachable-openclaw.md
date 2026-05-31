# VM Running But Unreachable — OpenCrawl (VM 104)

**Date:** 2026-05-26  
**Host:** pve1 (192.168.1.6)  
**VMID:** 104  
**Name:** OpenCrawl  
**Config:** 8 vCPU, 16 GB RAM, 50 GB disk, virtio NIC on vmbr0

## Presentation

`qm list` showed `104 OpenCrawl running`. But:
- No IP in ARP table for its MAC (`BC:24:11:34:78:03`)
- `qm guest cmd 104 network-get-interfaces` → "No QEMU guest agent configured"
- `qm terminal 104` → "unable to find a serial interface"
- No interface in `/proc/net/arp` matching the MAC

## Diagnosis

Checked the disk:

```bash
fdisk -l /dev/dm-8
```
```
GPT disklabel with 3 partitions:
  part1: 1M BIOS boot
  part2: 1G Linux filesystem
  part3: 49G Linux filesystem
```

```bash
blkid /dev/mapper/pve-vm--104--disk--0-part*
```
→ **No output** — partitions have no filesystem (no FSTYPE).

**Conclusion:** VM was created, disk was partitioned, but **no OS was ever installed**. The VM boots into a black screen (no bootable device).

## Next Steps (not executed)

- Attach a Linux distro ISO (Debian/Ubuntu) as the CD-ROM drive in the VM config
- Boot from ISO and install the OS
- Configure network during installation
- After installation: install QEMU guest agent (`apt install qemu-guest-agent`)

## Relevant Commands

```bash
# Check VM config
qm config 104

# Check disk partitions (need to resolve symlink)
ls -la /dev/pve/vm-104-disk-0  # -> ../dm-8
fdisk -l /dev/dm-8
blkid /dev/mapper/pve-vm--104--disk--0-part*

# Check network from host side
ip neigh | grep -i 'bc:24:11:34:78:03'
qm monitor 104 <<< 'info network'

# Check if serial console exists
qm terminal 104

# Attempt guest agent
qm guest cmd 104 network-get-interfaces
```
