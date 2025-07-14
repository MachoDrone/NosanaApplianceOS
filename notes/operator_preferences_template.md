# Operator Preference Template

Fill in your choices below each item, then save the file. We’ll integrate them into the architecture automatically.

1. Web-UI Security
   Choose one (or describe another):
   - [ ] WireGuard-only, no extra login
   - [ ] WireGuard + simple pass-phrase
   - [ ] WireGuard + TOTP (Google Authenticator)
   - [ ] WireGuard + hardware key / WebAuthn
   - Notes / Custom:

2. Text-Menu (TUI) Main Screen – Metrics to display (check all that apply):
   - [ ] GPU utilisation / temperature
   - [ ] Nosana job queue depth & current job
   - [ ] Active Docker containers
   - [ ] CPU & RAM usage
   - [ ] Network throughput
   - [ ] Power draw
   - [ ] Disk usage / SMART status
   - Other metrics:

   One-keystroke commands (check all that apply):
   - [ ] Restart Nosana container stack
   - [ ] Pull latest appliance updates
   - [ ] Reboot host
   - [ ] Tail logs of selected container
   - [ ] Clear old logs
   - Other commands:

3. Solana Wallet Backup & Restore
   Preferred methods (check all that apply):
   - [ ] Encrypted USB drive copy
   - [ ] Encrypted QR code export
   - [ ] Seed phrase
   - [ ] We do NOT want to document backup
   - Notes / Custom:

4. Immutable OS Hardening Level
   - [ ] Fully locked-down (no root writes)
   - [ ] Developer mode switch (temporary RW root)

   Extra safeguards (check all that apply):
   - [ ] Secure Boot
   - [ ] dm-verity
   - [ ] TPM / remote attestation (future)
   - Notes / Custom: