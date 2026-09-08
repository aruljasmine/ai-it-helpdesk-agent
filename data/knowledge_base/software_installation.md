# Software Installation Errors

## Common Symptoms
- Installer fails midway with a generic error code.
- "Access denied" or "administrator permission required" errors.
- Application installs but crashes immediately on launch.

## Common Causes
- Insufficient user permissions (standard user account instead of admin/managed install).
- Insufficient disk space.
- Corrupted installer download.
- Conflicting older version of the same software still partially installed.
- Antivirus quarantining the installer.

## Step-by-Step Troubleshooting
1. Check available disk space; most installers need at least 2-5 GB free temporarily.
2. Re-download the installer from the official company software portal (not a random external link) in case the file is corrupted.
3. Right-click the installer and choose "Run as administrator" (Windows), or install via the company's managed software centre if standard users cannot install software directly.
4. Uninstall any existing/older version of the application first, then restart before reinstalling.
5. Temporarily pause antivirus real-time protection during installation, then re-enable it afterward.
6. Check the installer log (usually in %TEMP% on Windows) for the specific error code, and search the vendor's documentation for that code.
7. Restart the computer and retry - many installer failures are resolved by clearing locked files/handles from a previous attempt.

## When to Escalate
Escalate if the software requires a licence key/seat allocation that IT must assign, or if installation requires elevated admin rights the user is not permitted to have.
