# Email Login Issues

## Common Symptoms
- "Incorrect username or password" despite entering the correct password.
- Email client keeps prompting for credentials repeatedly.
- Cannot log into webmail, but desktop app still works (or vice versa).

## Common Causes
- Recently changed password not yet updated in the saved/cached credentials.
- MFA prompt not being approved in time, or the MFA app/device is unreachable.
- Account temporarily locked from too many failed attempts.
- Email client using an outdated authentication protocol (e.g. Basic Auth deprecated in favour of Modern Auth/OAuth).
- Server-side mailbox issue or maintenance.

## Step-by-Step Troubleshooting
1. Confirm you can log into the company webmail portal in a browser first - this isolates whether the problem is the account or just the desktop client.
2. If you recently changed your password, remove the saved/cached credentials in the email client (Windows Credential Manager, or macOS Keychain Access) and re-enter the new password.
3. Approve any pending MFA push notification, or generate a fresh code if the previous one expired.
4. Fully close and reopen the email client, or remove and re-add the email account profile.
5. Check whether the email client supports Modern Authentication (OAuth); older configurations using Basic Auth may need to be reconfigured.
6. Verify the account is not locked by attempting the self-service password reset flow if login keeps failing.
7. Check the company status page for any announced email/mailbox server maintenance.

## When to Escalate
Escalate immediately if the user suspects unauthorized access to their mailbox (e.g. unfamiliar sent emails, mailbox rules they didn't create), since this is a potential security incident.
