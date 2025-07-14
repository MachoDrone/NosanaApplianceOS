# Nosana Appliance Fleet – Architecture & Operations Notes

_Last updated: 2025-07-14_

## 1. Goals & Constraints

1. Plug-and-play deployment of 1 – 50+ Nosana GPU hosts per operator, geographically distributed.
2. Automatic peer discovery so that **any** host can:
   • see the others (inventory)
   • stream live resource metrics (GPU, CPU, RAM, disk, network)
   • tail Docker logs / restart containers
   • dispatch pre-scripted commands (e.g. `wget … | bash`) securely
3. Fleet should be **immutable by default** – the core OS and Nosana host software are read-only and update atomically – while still letting operators optionally run **their own Docker containers** (e.g. extra monitoring or personal tools) on a separate writable partition.
4. Secure, zero-trust connectivity out-of-the-box. Each host carries a private key that we (Nosana) can never read – this is the operator’s **Solana wallet JSON** stored at `~/.nosana/nosana_key.json`.
5. Update channel for the OS image and built-in software that scales from 1 to 50 nodes: every host periodically checks a dedicated **GitHub repo** for signed release bundles (scripts, container image versions, config tweaks) and applies them automatically.

---

## 2. Network & Service Discovery

| Layer | Recommendation | Rationale |
|-------|----------------|-----------|
| Overlay VPN | **WireGuard-based mesh** (self-hosted Headscale controller or fully static mesh) | • Instant, zero-config NAT traversal<br>• Operators keep full control; **no third-party accounts or sign-ups**<br>• Headscale namespace (MagicDNS-compatible) gives each host a predictable FQDN (e.g. `node-12.gpu-farm.myfleet`) |
| Rendezvous / bootstrap | Operators receive a single-use auth key (environment variable or QR) they copy into the private config file. On first boot the host: <br>1. brings up WireGuard <br>2. registers itself (hostname, GPU inventory, public key, software version) to a lightweight registry (e.g. NATS JetStream or etcd) running **inside** the overlay | Avoids public IPs, scales to many operators, does not reveal topology to Nosana. |

Once on the mesh each node can reach all others privately; no inbound firewall holes required.

_Why Headscale?_  Headscale is the open-source control-plane for the Tailscale protocol.  We can ship it as a lightweight container that automatically starts on the **first** appliance or a tiny VPS the operator controls.  Nodes join with a single-use join key baked into their private config file, so zero interactive setup is needed.

For operators that prefer strictly peer-to-peer, we can fallback to a static WireGuard mesh file (`peers.conf`) generated during manufacturing, but Headscale is strongly recommended for NAT traversal and dynamic membership (add/remove hosts on demand).

_Scope clarification:_  All discovery and overlay networking is **per-operator**.  Nodes owned by different operators never see each other, even if they share the same Headscale server.

---

## 3. Fleet Management Components

1. **nosana-agent (container, per-host)**
   • exposes gRPC for: metrics push, command execution, Docker log streaming.
   • ships Prometheus node_exporter & DCGM exporter for NVIDIA stats.
2. **nosana-controller (container, any host)**
   • optional; if running, subscribes to the registry and builds a live UI (React + Grafana) showing all nodes.
   • CLI (`nosana fleet …`) uses the same gRPC API; can run from a laptop on the mesh.
3. **Portainer-CE (optional)** – GUI for Docker management over the overlay.

_All artifacts are delivered as signed Docker images pulled from GHCR._

---

## 4. Immutable OS & Update Strategy

| Layer | Technology | Update Flow |
|-------|------------|-------------|
| Base OS | **Ubuntu Core 24** or **Debian Bookworm + OSTree** image | • Read-only root FS, A/B partition + atomic rollback
• `nosana-updater` service checks GitHub Releases (signed) daily → downloads new OSTree commit, triggers reboot when idle |
| Drivers / NVIDIA | Host-OS level, version pinned in the image | Updated together with the OS image to guarantee compatibility. |
| Application stack | Docker Compose bundle (`nosana-agent`, etc.) | Version pinned via SHA in `/opt/nosana/docker-bundle.yml`. Updater swaps the file & restarts Compose. |

Removing packages = ship a new immutable image that simply omits them.

Operators can still run **their own containers** – stored on `/var/lib/docker`, a separate RW partition not touched by system update.

> **Note**: We are _not_ redesigning the Nosana host software itself.  The containers listed below refer to supporting services shipped with the appliance OS; the actual compute agent follows the existing installation steps in [Nosana docs](https://docs.nosana.com/hosts/grid-ubuntu.html).

---

## 5. Remote Script Execution (Optional)

Operators may choose to enable a **“script switchboard”**: small shell scripts stored in the same GitHub repo as the update channel.  Each script is described by a YAML manifest (name, description, command).  When the operator flips a feature switch in the UI, the appliance pulls the script and runs it locally, streaming stdout/err back to the requester over WireGuard.

No third-party accounts are required, and signing is optional—if you prefer added safety we can extend this later with GPG-signed commits.

---

## 6. UI / Operator Interfaces

| Focus | Approach | Key Points |
|-------|----------|------------|
| **6.1 Web Interface** | Progressive Web App (React + Tailwind, served by `nosana-agent`) | • Accessible via HTTPS over WireGuard from any phone or desktop<br>• Mobile-first layout: card view, swipe-friendly actions, dark-mode default<br>• Installs like an app (“Add to Home Screen”) and works offline via ServiceWorker<br>• Same host can serve the UI even when the rest of the fleet is unreachable |
| **6.2 Local Text UI** | Terminal User Interface (Python Textual or Go BubbleTea) | • Available on the local console (HDMI/keyboard) **and** over SSH<br>• Mirrors all web features: metrics dashboard, logs tail, script launcher<br>• Auto-starts if web UI is unreachable or when no HDMI is present |
| **6.3 Feature Parity** | Single gRPC/HTTP API | • Both UIs call the same endpoints defined in a shared protobuf<br>• Command catalogue stored in YAML → automatically rendered in both UIs<br>• CI checks ensure new API methods are implemented by both clients before release |
| **6.4 No External Dependencies** | Served directly from each host | • Static web assets bundled into the `nosana-agent` image<br>• TUI binary shipped alongside the agent; no package installs needed at runtime |
| **6.5 Mobile-First UX** | Design / Accessibility | • Touch targets ≥ 48 px, readable fonts, high-contrast palette<br>• Network-loss tolerant: caches last 24 h of metrics locally<br>• Quick-action buttons for common scripts (restart container, purge logs) |

---

## 7. Open Questions / Next Steps

1. **Key provisioning** – best UX for injecting the per-operator WireGuard key during manufacturing? USB, QR, cloud init?
2. **Registry location** – should we run a tiny VPS per operator for the NATS/etcd rendezvous, or allow any node to self-elect leader?
3. **Compliance & audit** – is tamper-evidence (e.g. TPM measured boot, remote attestation) a requirement? (future consideration)
4. **Offline sites** – currently out of scope as hosts are expected to be online.
5. **Operator UX** – confirm whether touch-friendly buttons are preferred over text inputs on phones.

Feel free to refine these points or add new requirements.

---

### Are we asking the right questions?

Mostly yes – connectivity, fleet discovery, and update cadence are the core challenges. Additional aspects worth considering:

• Disaster recovery: what happens if an OS update bricks 50 nodes? Rollback plan?
• Observability at scale: metrics retention, alerting, logs storage duration.
• Licensing: NVIDIA drivers & CUDA redistribution constraints.

---

## 8. Operator Preferences (Finalised)

Below decisions reflect the recommended defaults based on operator feedback and simplicity requirements.

1. **Web-UI Security**  
   • Primary gate is the WireGuard overlay; only devices that possess the WireGuard key can reach the HTTPS endpoint.  
   • **Mobile devices (phones / tablets)** must enter a 4–6-digit PIN before the UI loads.  
   • **PCs / laptops / local host consoles** authenticate with the operator’s normal Ubuntu username + password (or just the password if the screen is already unlocked).  
   • PIN hashes are stored (bcrypt) on the writable partition and can be reset from the TUI.

2. **Text-Menu (TUI) Main Screen**  
   _Metrics shown at a glance_  
   • GPU utilisation & temperature (per card)  
   • CPU & RAM usage  
   • Active Docker containers status  
   • Power draw (per host)  
   • One-line host health summary (up, down, frozen)  
   _One-keystroke actions_  
   • Start host (`./starthost.sh`)  
   • Stop host (`./stophost.sh`)  
   • Reboot host (`./reboot.sh`)

3. **Solana Wallet Backup & Restore**  
   • Wallet backup & restore moves into the Web UI: operators can **download** or **upload** the encrypted key from any Windows/macOS/Linux laptop or phone.  
   • Two options offered: save to an **encrypted USB drive** or display/save an **encrypted QR code** for printing.  
   • Nosana never sees or stores the private key.

4. **Immutable OS Hardening**  
   • Full hardening strategy **TBD** — decisions postponed until the Nosana host software is fully assessed.  
   • Current prototype keeps the base image read-only but does **not** enable Secure Boot / dm-verity yet.  
   • A future “developer mode” and additional safeguards will be revisited once requirements are clearer.

---

**End of document**