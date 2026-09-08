# Printer Problems

## Common Symptoms
- "Cannot print documents" / print job stuck in the queue.
- Printer shows as offline.
- Print quality issues (streaks, faded text).

## Common Causes
- Print spooler service stuck or crashed.
- Printer not set as default, or wrong printer selected.
- Network printer lost its IP address (DHCP lease renewed).
- Low toner/ink, or a paper jam.
- Outdated or corrupted printer driver.

## Step-by-Step Troubleshooting
1. Check the printer's physical display for error messages (paper jam, low toner, offline).
2. Confirm the printer is powered on and connected to the same network as your computer.
3. Clear the print queue: open "Printers & Scanners", select the printer, cancel all stuck jobs.
4. Restart the Print Spooler service (Windows: Services app > Print Spooler > Restart).
5. Remove the printer and re-add it, letting the OS reinstall the driver automatically.
6. Set the correct printer as the default printer if multiple are installed.
7. For network printers, verify the printer's IP address hasn't changed (check printer settings menu vs. what your computer has saved).
8. Try printing a test page directly from the printer's own control panel to isolate a printer-hardware issue from a computer/driver issue.

## When to Escalate
Escalate if the printer is a shared network device affecting an entire team/floor, or if hardware appears physically faulty (grinding noises, error lights that persist after a restart).
