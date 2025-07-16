"""
why_remaster5edits.py  –  Rationale for the design and code choices in remaster5.py

This file is **documentation only**.  It lives next to remaster5.py so future
maintainers (human or AI) understand WHY things look the way they do and which
parts must remain unchanged unless this file is also updated.

Created after remaster5.py (copy of remaster4.py) – July 2025
Last update: <fill-in-when-editing>
"""

# -----------------------------------------------------------------------------
# 1. Autoinstall design  (user-data / meta-data / GRUB menu)
# -----------------------------------------------------------------------------
# • Everything (YAML, meta-data, GRUB entries) is embedded directly in the
#   Python source so *one single file* can remaster an ISO.  This keeps the
#   tool portable and avoids path-resolution problems in CI or when users copy
#   the script to a fresh machine.
#
# • Interactive “orange” screens (locale, keyboard, network, proxy, apt,
#   storage, identity, ubuntu-pro, drivers) are *deliberately* left untouched.
#   The target workflow is: install a *minimised* Ubuntu Server image (no snap,
#   no OpenSSH) and then run a first-boot script that installs all remaining
#   apps in one go.  Automating only the mandatory parts guarantees the user
#   still answers site-specific questions correctly.
#
# • `updates: security` was removed from user-data because, during development,
#   its presence broke the proxy-configuration & mirror-testing screens.  The
#   current minimal YAML lets those UIs appear normally.
#
# • `source.id` is pinned to **ubuntu-server-minimal** as a baseline for an
#   eventual *immutable OS* conversion.  Future work may add HWE kernels or
#   extra NIC drivers but the minimal seed stays for compliance & footprint.
#
# • Late-commands fetch and execute `late.sh` from GitHub.  The maintainer keeps
#   that script under version control; if the network is down the install still
#   completes (late.sh jobs are optimisations only).
#
# • Serial console parameters (`console=ttyS0,115200n8`) are *not required* and
#   may be removed in a future security-hardening pass.
#
# • GRUB timeout is 30 s so testers don’t miss the menu during rapid iteration.
#   Manual & “Try” menu entries remain for troubleshooting; they will be pruned
#   once the automated path is final.

# -----------------------------------------------------------------------------
# 2. HelloNOS test artefacts
# -----------------------------------------------------------------------------
# • `HelloNOS.ESP`, `HelloNOS.BOOT`, `HelloNOS.OPT` were research probes to
#   learn where custom bytes survive the Subiquity install.
#   – OPT persistence is *no longer required*; code kept for possible future use.
#   – Offsets (ESP +1024, MBR +512) follow guidance in
#     HybridRemasterInstructions.txt and may change if a new Ubuntu ISO layout
#     demands it.
#   – No redundant copies are injected; one copy is enough for the current audit
#     goals and avoids extra risk of corrupting boot sectors.

# -----------------------------------------------------------------------------
# 3. ISO build mechanics
# -----------------------------------------------------------------------------
# • MBR template: only the first 432 bytes are extracted (xorriso expects the
#   bootstrap code *without* the 14-byte partition table).
# • Fallback `dd skip=6608 count=11264` values came straight from
#   HybridRemasterInstructions.txt (22.04 desktop) and still match 24.04 Server
#   – they run only if dynamic fdisk parsing fails.
# • Three build pipelines exist because early AI attempts hit environments where
#   xorriso lacked GPT flags.  Order: xorriso → genisoimage(+joliet-long) →
#   genisoimage(basic).
# • `-partition_offset 16` and the EFI-partition GUID are copied from Canonical
#   docs to maximise firmware compatibility.

# -----------------------------------------------------------------------------
# 4. Dependencies & environment assumptions
# -----------------------------------------------------------------------------
# • System deps: python3-pip, xorriso, coreutils(dd), *binwalk* (debug helper).
#   Binwalk is not used by the script itself; it is handy for manual inspection
#   of the rebuilt ISO.
# • Python deps: requests + tqdm chosen purely for nice download progress.
#   A six-command fall-through installs them regardless of the host’s pip setup.
# • Script always runs on bare-metal with sudo access; not designed for
#   rootless containers.

# -----------------------------------------------------------------------------
# 5. Cleanup & post-install minimisation
# -----------------------------------------------------------------------------
# • cleanup-minimal.sh disables *snapd* (does NOT purge it) and masks its
#   services.  Snap may be re-enabled later once the image moves to an
#   immutable model.
# • The script is left for *manual* execution so admins can inspect a fresh
#   install first.
# • Package count printout is informational only.

# -----------------------------------------------------------------------------
# 6. File-placement redundancy
# -----------------------------------------------------------------------------
# • Autoinstall files are written to *both* /server/ and the ISO root, plus
#   YAML & YML variants, because different Subiquity versions probe different
#   paths.  Empty vendor- and network-data files satisfy the datasource without
#   overriding anything.

# -----------------------------------------------------------------------------
# 7. Command-line interface & flags
# -----------------------------------------------------------------------------
# • `-hello` is the canonical flag (early typo `-hellow` abandoned).
# • No additional flags required right now; future ideas include `--no-snap` or
#   `--iso <url>` but those will be added alongside a bump to remaster6.py and
#   an update to this document.

# -----------------------------------------------------------------------------
# 8. Edge cases & deferred features
# -----------------------------------------------------------------------------
# • Download resume, SHA256 verification, SELinux/AppArmor hardening – postponed
#   until the core remaster flow is final.
# • ISO URL is hard-coded for reproducibility; will become a CLI parameter in a
#   later version if needed.

# -----------------------------------------------------------------------------
# 9. Maintenance policy
# -----------------------------------------------------------------------------
# • This file **must be updated** whenever a change to remaster5.py (or its
#   successors) would surprise a maintainer who has only read this rationale.
# • Version bump rule: once a *difficult* edit is stable, save the next script
#   as remaster6.py and clone this file accordingly.
# -----------------------------------------------------------------------------