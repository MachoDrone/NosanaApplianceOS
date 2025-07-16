"""
why_remaster5edits.py
=====================
Documentation-only companion to `remaster5.py`.
Keeps a human-readable record of *why* particular code paths, flags and
constants exist so future edits (manual or AI) respect the original intent.

This file should be updated **every time** an invariant described here changes
or when `remaster5.py` evolves into `remaster6.py`, `remaster7.py`, …

Last update: 2025-07-16
Author/maintainer: <fill when editing>
"""

# -----------------------------------------------------------------------------
# 0. Philosophy
# -----------------------------------------------------------------------------
# • One-file portability – Users download a single Python script (remasterX.py)
#   plus a stock Ubuntu ISO and immediately remaster.  No external templates or
#   YAML files are needed, avoiding path headaches and simplifying hand-offs
#   to less technical operators.
# • All choices below are *user-confirmed*.  Do **not** alter them without also
#   updating this rationale and confirming with the maintainer.

# -----------------------------------------------------------------------------
# 1. Autoinstall design (embedded YAML & GRUB menu)
# -----------------------------------------------------------------------------
# 1.1  Embedded user-data / meta-data
#      – Keeps the tool self-contained and easy to version-control.
#      – Updates go through script revision control; no risk of stale external
#        files.
#
# 1.2  Interactive (“orange”) screens intentionally *left interactive*
#      – Required inputs: locale, keyboard, **proxy & mirror test**, storage,
#        identity, driver selection.
#      – The install must remain *semi-automated*: Ubuntu Server minimal base
#        only, no snap, no OpenSSH.  A separate first-boot script adds the real
#        application stack.
#
# 1.3  `updates: security` key removed
#      – Earlier attempts suppressed the proxy & mirror test screens; with the
#        key deleted both screens now appear and function.
#
# 1.4  `source.id: ubuntu-server-minimal`
#      – Baseline image for a future immutable OS.  Extra HWE kernels or NIC
#        drivers might be injected later, but the minimal seed stays.
#
# 1.5  Late-commands fetch `late.sh` from GitHub
#      – Maintainer owns and updates that script.  Network failure is
#        acceptable: install still completes with a basic system.
#
# 1.6  GRUB configuration
#      – Serial console parameter (`console=ttyS0,115200n8`) currently present
#        but flagged as an *eventual security removal*.
#      – Timeout 30 s so testers don’t miss the menu during development.
#      – “Manual install” & “Try without installing” remain temporarily for
#        reference; plan to prune after workflow stabilises.

# -----------------------------------------------------------------------------
# 2. HelloNOS test artefacts
# -----------------------------------------------------------------------------
# • Purpose: experimental markers to learn which ISO regions survive an
#   installation.  No production requirement at this time.
# • `HelloNOS.OPT` persistence is **NOT** required now; code retained for
#   possible future forensic needs.
# • Offsets chosen by AI per HybridRemasterInstructions.txt guidance:
#       – ESP  +1024 bytes (inside FAT32 header slack)
#       – MBR  +512  bytes (after bootstrap code, before PT)
#   These may need adjustment for different Ubuntu ISOs.
# • Only one copy of each marker is written – redundancy deemed unnecessary and
#   could endanger boot integrity.

# -----------------------------------------------------------------------------
# 3. ISO build mechanics & magic constants
# -----------------------------------------------------------------------------
# 3.1  MBR template size 432 B
#      – xorriso’s `--grub2-mbr` expects bootstrap code *without* the 14-byte
#        partition table (446-14 = 432).
#
# 3.2  EFI fallback extraction
#      – `dd skip=6608 count=11264` copied from Thomas Schmitt’s example in
#        HybridRemasterInstructions.txt (Ubuntu 22.04 desktop) and still works
#        for 24.04.2 server.  Runs only if dynamic fdisk parsing fails.
#
# 3.3  Triple build pipeline order
#      1. xorriso (preferred hybrid GPT/MBR)
#      2. genisoimage + joliet-long (older distros where xorriso lacks GPT)
#      3. Plain genisoimage (fallback BIOS-only)
#      This odd sequence originated from AI troubleshooting sessions but now
#      serves as defensive coding across heterogeneous builder hosts.
#
# 3.4  `-partition_offset 16` & EFI partition-type GUID 28732ac1-1ff8-…
#      – Copied from Canonical’s own command line; known to satisfy finicky
#        UEFI firmware.

# -----------------------------------------------------------------------------
# 4. Dependency strategy
# -----------------------------------------------------------------------------
# • System packages: python3-pip, xorriso, coreutils(dd), **binwalk** (developer
#   aid for inspecting ISO contents).
# • Python packages: requests + tqdm strictly for nicer download progress.
# • Six-command pip install loop exists because early AI attempts ran on hosts
#   with wildly different pip setups; kept for maximum resilience.
# • Runtime `apt-get` happens on the build workstation only – always bare metal
#   with sudo access.  Not designed for restricted containers.

# -----------------------------------------------------------------------------
# 5. Post-install minimisation (cleanup-minimal.sh)
# -----------------------------------------------------------------------------
# • Goal: disable snap services (mask) and optionally remove packages.  The
#   maintainer prefers *disable only*; script currently performs a purge – to be
#   revisited in remaster6.py.
# • Script is manual so admins can inspect a fresh install first.
# • Final line prints package count purely for human verification.

# -----------------------------------------------------------------------------
# 6. Autoinstall file redundancy
# -----------------------------------------------------------------------------
# • Files written to both `/server/` and ISO root plus `autoinstall.yaml` and
#   `.yml` because Subiquity version detection was unreliable in past tests.
# • Empty vendor-data & network-data files satisfy datasource completeness
#   without overriding config.  No misbehaviour observed.

# -----------------------------------------------------------------------------
# 7. CLI flags
# -----------------------------------------------------------------------------
# • Current flags:  -dc (no cleanup)   -hello (inject HelloNOS)   -autoinstall
# • Typo `-hellow` abandoned; no backward compatibility.
# • Future ideas (not implemented): --no-snap, --iso <url>.

# -----------------------------------------------------------------------------
# 8. Edge cases / deferred work
# -----------------------------------------------------------------------------
# • No resumable download, ISO checksum or SELinux/AppArmor tweaks yet – deemed
#   unnecessary until core flow finalised.
# • ISO URL hard-coded to 24.04.2 for reproducibility; may become a flag later.

# -----------------------------------------------------------------------------
# 9. Maintenance & versioning policy
# -----------------------------------------------------------------------------
# • When a *difficult* change lands and stabilises, save the new script as the
#   next sequential `remasterN.py` and clone this doc accordingly.
# • Always update this file when:
#   – Any constant here changes (offsets, GUIDs, GRUB params, etc.)
#   – New CLI flags are added or semantics change.
#   – Behaviour that users rely on is modified.
# -----------------------------------------------------------------------------