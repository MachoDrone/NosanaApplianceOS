# Operator Preference Template

Fill in your choices below each item, then save the file. We’ll integrate them into the architecture automatically.

1. Web-UI Security
   Choose one (or describe another):
   - [x] WireGuard-only, no extra login
   - [ ] WireGuard + simple pass-phrase
   - [ ] WireGuard + TOTP (Google Authenticator)
   - [ ] WireGuard + hardware key / WebAuthn
   - Notes / Custom:

2. Text-Menu (TUI) Main Screen – Metrics to display (check all that apply):
   - [x] GPU utilisation / temperature
   - [x] Nosana job queue depth & current job
   - [x] Active Docker containers
   - [x] CPU & RAM usage
   - [ ] Network throughput
   - [ ] Power draw
   - [ ] Disk usage / SMART status
   - Other metrics:

   One-keystroke commands (check all that apply):
   - [x] Restart Nosana container stack
   - [x] Pull latest appliance updates
   - [x] Reboot host
   - [x] Tail logs of selected container
   - [x] Clear old logs
   - Other commands:

3. Solana Wallet Backup & Restore
   Preferred methods (check all that apply):
   - [x] Encrypted USB drive copy
   - [x] Encrypted QR code export
   - [ ] Seed phrase
   - [ ] We do NOT want to document backup
   - Notes / Custom:

4. Immutable OS Hardening Level
   - [ ] Fully locked-down (no root writes)
   - [x] Developer mode switch (temporary RW root)

   Extra safeguards (check all that apply):
   - [x] Secure Boot
   - [x] dm-verity
   - [ ] TPM / remote attestation (future)
   - Notes / Custom: