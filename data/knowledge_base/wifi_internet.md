# Wi-Fi and Internet Connectivity Problems

## Common Symptoms
- Connected to Wi-Fi but no internet access ("no internet, secured").
- Wi-Fi network not appearing in the list.
- Frequent disconnects or very slow speeds.

## Common Causes
- Router/modem needs a restart, or an ISP outage.
- Incorrect DNS settings.
- Too many devices on the same band causing congestion.
- Outdated Wi-Fi adapter driver.
- IP address conflict on the local network.

## Step-by-Step Troubleshooting
1. Restart the router and modem: unplug both for 30 seconds, plug the modem in first, wait 1 minute, then the router.
2. On the affected device, forget the Wi-Fi network and reconnect with the password.
3. Run the built-in network troubleshooter (Windows: Settings > Network & Internet > Status > Network troubleshooter; macOS: Wireless Diagnostics app).
4. Check if other devices on the same network also lack internet access. If yes, the issue is the router/ISP, not the device.
5. Try switching from the 5GHz band to the 2.4GHz band (or vice versa) if the router offers both.
6. Flush the DNS cache: Windows `ipconfig /flushdns`, macOS `sudo dscacheutil -flushcache`.
7. Update the Wi-Fi adapter driver from Device Manager (Windows) or via System Update (macOS).
8. If using a company VPN, temporarily disconnect it to rule out a VPN routing issue.

## When to Escalate
Escalate if the outage affects multiple users/floors simultaneously, or if step 1-7 do not resolve a single user's issue after two attempts.
