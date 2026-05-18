# Scheduled Audits

SilentSpace Guardian includes three scheduled audit workflows. Each runs a
Python script that audits all meeting JSON files and writes a Markdown report.
Scheduling is handled by the operating system — cron on Linux/macOS/WSL,
Windows Task Scheduler on native Windows.

None of these are installed automatically. Setup is manual and transparent.

---

## The Three Workflows

### A. Daily Meeting Regret Audit

**When:** Weekdays at 5 PM
**Output:** `reports/daily_digest.md`
**Script:** `scripts/run_daily_regret_audit.sh`

Reviews all meeting files, identifies the top waste offenders, and lists all
async candidates (meetings that should have been emails). Files the report
at end of day.

```bash
bash scripts/run_daily_regret_audit.sh
```

### B. Weekly Entropy Summary

**When:** Fridays at 4 PM
**Output:** `reports/weekly_entropy.md`
**Script:** `scripts/run_weekly_entropy_summary.sh`

Focuses on recurring meetings: their cadence, cumulative waste, and estimated
weekly person-hours lost. Identifies structural entropy patterns.

```bash
bash scripts/run_weekly_entropy_summary.sh
```

### C. Morning Preflight Audit

**When:** Weekday mornings at 7 AM
**Output:** `reports/preflight_report.md`
**Script:** `scripts/run_preflight_audit.sh`

Scans all meeting files and flags likely async candidates before the day
begins. A meeting is flagged if it meets two or more of: `could_be_email`,
no agenda, no action items, waste score ≥ 60.

```bash
bash scripts/run_preflight_audit.sh
```

---

## Manual Verification

Run any script manually and inspect the output:

```bash
bash scripts/run_daily_regret_audit.sh && cat reports/daily_digest.md
bash scripts/run_weekly_entropy_summary.sh && cat reports/weekly_entropy.md
bash scripts/run_preflight_audit.sh && cat reports/preflight_report.md
```

All three scripts exit 0 on success. They print the report path and a
brief summary to stdout.

---

## Linux, macOS, and WSL — Cron Setup

Open your crontab:

```bash
crontab -e
```

Add entries (adjust the path to match your installation):

```cron
# Daily regret audit — weekdays at 5 PM
0 17 * * 1-5 cd /path/to/silentspace-guardian && bash scripts/run_daily_regret_audit.sh >> logs/daily.log 2>&1

# Weekly entropy summary — Fridays at 4 PM
0 16 * * 5   cd /path/to/silentspace-guardian && bash scripts/run_weekly_entropy_summary.sh >> logs/weekly.log 2>&1

# Morning preflight — weekdays at 7 AM
0 7  * * 1-5 cd /path/to/silentspace-guardian && bash scripts/run_preflight_audit.sh >> logs/preflight.log 2>&1
```

Create the logs directory if needed:

```bash
mkdir -p logs
```

Verify cron is running:

```bash
# macOS
sudo brew services start cron

# Linux/WSL
sudo service cron start
# or
sudo systemctl start cron
```

### WSL-Specific Notes

WSL does not run cron automatically at system startup. Options:

1. **Manual start:** `sudo service cron start` in your WSL terminal before relying on scheduled jobs
2. **Windows Task Scheduler + WSL:** Create a Windows task that runs `wsl bash /path/to/silentspace-guardian/scripts/run_daily_regret_audit.sh`
3. **Startup script:** Add `sudo service cron start` to `/etc/wsl.conf` via `[boot]` command (WSL2 only):

```ini
# /etc/wsl.conf
[boot]
command = service cron start
```

---

## Windows — Task Scheduler

For native Windows (without WSL for scheduling), use Windows Task Scheduler
to call the Python scripts directly via PowerShell.

### Create a Task (PowerShell)

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "python\generate_daily_digest.py" `
    -WorkingDirectory "C:\path\to\silentspace-guardian"

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "5:00PM"

Register-ScheduledTask `
    -TaskName "SilentSpace Daily Regret Audit" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest
```

Repeat for the other two workflows, adjusting the script and trigger.

### Create a Task (GUI)

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Task**
3. **General:** Name = `SilentSpace Daily Regret Audit`
4. **Triggers:** New → Daily → Recur every 1 days → set time to 5:00 PM
   → Advanced: repeat on Mon–Fri only
5. **Actions:** New → Start a program
   - Program: `python`
   - Arguments: `python\generate_daily_digest.py`
   - Start in: `C:\path\to\silentspace-guardian`
6. Click OK and save.

---

## What Is Mocked

The meeting JSON files in `meetings/` are fictional. The scheduled audits run
against this fixed set — there is no live calendar integration. When real
calendar integration is added, the scripts will be updated to pull from it.

For now: the reports are real, the scores are real, the meetings are not.
