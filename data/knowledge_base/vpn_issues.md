# VPN Connection Problems

## Common Symptoms
- VPN client stuck on "Connecting..." and then times out.
- Connects, but internal company resources are unreachable.
- VPN disconnects randomly after a few minutes.

## Common Causes
- Expired VPN credentials or expired client certificate.
- Local firewall or antivirus blocking the VPN's ports/protocol.
- Outdated VPN client software.
- Weak/unstable home internet connection.
- Company VPN server maintenance or outage.

## Step-by-Step Troubleshooting
1. Confirm your internet connection works without the VPN first (open any website).
2. Fully close and reopen the VPN client, then retry the connection.
3. Restart your computer - this clears stuck network adapters the VPN client relies on.
4. Check the VPN client version and update it if a newer version is available.
5. Temporarily disable third-party antivirus/firewall software and retry (re-enable it afterward regardless of outcome).
6. Re-enter your VPN credentials manually rather than using a saved/cached password, in case it expired.
7. If connected but resources are unreachable, confirm split-tunneling settings are correct and that you're on the intended VPN profile (e.g. "Full Office Access" vs "Guest").
8. Check the company IT status page for any announced VPN server maintenance.

## When to Escalate
Escalate if VPN certificates appear expired/invalid (this usually needs an admin to reissue them), or if multiple users report the same outage at the same time.
