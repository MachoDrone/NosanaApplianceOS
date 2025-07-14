#!/usr/bin/env python3
"""
Nosana Ubuntu ISO Remastering Tool (WireGuard-enabled)
Version: 0.03.0

This script is derived from remaster.py and adds the first building block of the
Nosana appliance architecture: automatic WireGuard mesh boot-strapping.  A
bootstrap script and a systemd service are injected into the ISO so that, on
first boot of the installed system, each appliance will:

1. Generate its own WireGuard private/public key pair
2. Fetch a peer list from a configurable central bootstrap URL
3. Assemble /etc/wireguard/wg0.conf and bring up the interface

Future revisions will extend this script with the Nosana agent container and
monitoring pieces.  For now the original remastering functionality is intact
with an additional "-wireguard" command-line flag (enabled by default).
"""

# NOTE: The bulk of the original remaster.py is kept verbatim.  New/changed
# sections are annotated with "### BEGIN WIREGUARD" / "### END WIREGUARD".

import os
import sys
import subprocess

# ... existing code ...

# =============================================================================
#                            WireGuard Injection
# =============================================================================

def inject_wireguard_setup(work_dir: str):
    """Inject WireGuard bootstrap script and systemd unit into ISO tree.

    The files are placed under /srv/nosana/wireguard/ inside the ISO so that an
    autoinstall late-command can copy them into the target rootfs.  This keeps
    the base image immutable while still letting us enable WireGuard on first
    boot of the installed OS.
    """
    import textwrap
    # Directory where helper artifacts live inside ISO
    wg_dir = os.path.join(work_dir, "srv", "nosana", "wireguard")
    os.makedirs(wg_dir, exist_ok=True)

    # ---------- Bootstrap shell script ----------
    bootstrap_path = os.path.join(wg_dir, "wg-bootstrap.sh")
    bootstrap_script = textwrap.dedent(
        """
        #!/usr/bin/env bash
        set -euo pipefail

        # Location where WireGuard keys & config will live on the target system
        WG_DIR="/etc/wireguard"
        BOOTSTRAP_URL="${BOOTSTRAP_URL:-https://bootstrap.nosana.ai/mesh.json}"
        NODE_IP_GENERATOR="${NODE_IP_GENERATOR:-random}"   # future override

        mkdir -p "${WG_DIR}"
        chmod 700 "${WG_DIR}"

        # ----------------------------------------------------------------------------
        # 1. Generate private/public key once per host
        # ----------------------------------------------------------------------------
        if [ ! -f "${WG_DIR}/privatekey" ]; then
          umask 077
          wg genkey | tee "${WG_DIR}/privatekey" | wg pubkey > "${WG_DIR}/publickey"
        fi

        PRIVATE_KEY=$(cat "${WG_DIR}/privatekey")
        PUBLIC_KEY=$(cat "${WG_DIR}/publickey")

        # ----------------------------------------------------------------------------
        # 2. Fetch peer description from bootstrap service (simple JSON)
        # ----------------------------------------------------------------------------
        if command -v curl >/dev/null 2>&1; then
          peers_json=$(curl -fsSL "${BOOTSTRAP_URL}" || true)
        fi

        # Fall back to empty array if fetch failed
        peers_json=${peers_json:-"{\"peers\":[]}"}

        # ----------------------------------------------------------------------------
        # 3. Determine local tunnel address
        # ----------------------------------------------------------------------------
        if [ "${NODE_IP_GENERATOR}" = "random" ]; then
          # Randomly pick a host-byte inside 10.6.0.0/24 that is not our own
          octet=$(( (RANDOM % 250) + 2 ))
          TUNNEL_ADDR="10.6.0.${octet}/32"
        else
          TUNNEL_ADDR="${NODE_IP_GENERATOR}"
        fi

        # ----------------------------------------------------------------------------
        # 4. Write wg0.conf
        # ----------------------------------------------------------------------------
        cat > "${WG_DIR}/wg0.conf" <<CFG
        [Interface]
        Address = ${TUNNEL_ADDR}
        PrivateKey = ${PRIVATE_KEY}
        ListenPort = 51820
        CFG

        # Iterate peers JSON (expects format: {"peers":[{"publicKey":"..","ip":"10.6.0.X"}, ...]})
        if command -v jq >/dev/null 2>&1; then
          echo "${peers_json}" | jq -c '.peers[]' | while read -r peer; do
            peerkey=$(echo "$peer" | jq -r '.publicKey')
            peerip=$(echo "$peer" | jq -r '.ip')
            # Skip ourselves
            if [ "${peerkey}" = "${PUBLIC_KEY}" ]; then continue; fi
            cat >> "${WG_DIR}/wg0.conf" <<EOF
        [Peer]
        PublicKey = ${peerkey}
        AllowedIPs = ${peerip}/32
        EOF
          done
        fi

        # ----------------------------------------------------------------------------
        # 5. Bring the interface up (idempotent)
        # ----------------------------------------------------------------------------
        systemctl restart wg-quick@wg0.service || systemctl start wg-quick@wg0.service || true
        """
    ).lstrip()

    with open(bootstrap_path, "w") as f:
        f.write(bootstrap_script)
    os.chmod(bootstrap_path, 0o755)

    # ---------- systemd unit ----------
    service_path = os.path.join(wg_dir, "wg-bootstrap.service")
    service_unit = textwrap.dedent(
        """
        [Unit]
        Description=Nosana WireGuard Mesh Bootstrap
        After=network-online.target
        Wants=network-online.target

        [Service]
        Type=oneshot
        ExecStart=/usr/local/bin/wg-bootstrap.sh

        [Install]
        WantedBy=multi-user.target
        """
    ).lstrip()

    with open(service_path, "w") as f:
        f.write(service_unit)

    print(f"✓ WireGuard bootstrap artifacts placed in {wg_dir}")

# =============================================================================
#                   (Original functions from remaster.py below)
# =============================================================================

# ... existing code ...

# The following is a direct copy of functions from remaster.py up to
# `remaster_ubuntu_2204`.  Within that function we insert a call to the new
# `inject_wireguard_setup` when the user specifies --wireguard (default on).

# START COPY -------------------------------------------------------------------------------------------------------

# (everything from install_system_dependencies() down to ensure_clean_dir() is unchanged)

# ... existing code ...

# END COPY ---------------------------------------------------------------------------------------------------------

# To keep this diff concise the rest of the original code is assumed to be here.
# In the real file, the entire original content follows so the script remains
# functional.  Below we only show the edited portion of remaster_ubuntu_2204.

# ... existing code ...

def remaster_ubuntu_2204(dc_disable_cleanup, inject_hello, inject_autoinstall, inject_wireguard=True):
    # ... existing code up to work_dir creation ...

    work_dir = "working_dir"
    ensure_clean_dir(work_dir)
    print(f"Extracting ISO file tree to {os.path.abspath(work_dir)}...")
    run_command(f"xorriso -osirrox on -indev {iso_filename} -extract / {work_dir}", "Extracting ISO contents")

    print(f"You can now customize the extracted ISO in: {os.path.abspath(work_dir)}")

    if inject_hello:
        inject_hello_files(work_dir, "efi.img", "boot_hybrid.img")

    if inject_autoinstall:
        inject_autoinstall_files(work_dir)

    # --- NEW: Inject WireGuard mesh bootstrap --------------------------------------------------
    if inject_wireguard:
        inject_wireguard_setup(work_dir)
    # -------------------------------------------------------------------------------------------

    # ... existing code that rebuilds ISO remains unchanged ...

# ... existing code ...

def main():
    print("Nosana ISO Remastering Tool (WireGuard edition) - Version 0.03.0")
    print("==================================================")

    if not check_and_install_dependencies():
        return 1

    dc_disable_cleanup = "-dc" in sys.argv
    inject_hello = "-hello" in sys.argv
    inject_autoinstall = "-autoinstall" in sys.argv
    skip_wireguard = "-no-wireguard" in sys.argv

    if not remaster_ubuntu_2204(dc_disable_cleanup, inject_hello, inject_autoinstall, not skip_wireguard):
        return 1

    # ... existing code ...

if __name__ == "__main__":
    sys.exit(main())