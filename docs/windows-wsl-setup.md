# Windows Setup Guide: WSL2 + Ubuntu + GnuCOBOL

SilentSpace Guardian auto-detects WSL and compiles the COBOL entropy engine
for you on first run. This guide walks through installing the required tools
so that first run actually works.

---

## What Is WSL2?

Windows Subsystem for Linux 2 (WSL2) lets you run a real Linux environment —
including Ubuntu — directly inside Windows, with no virtual machine or dual
boot required. SilentSpace Guardian uses it to access GnuCOBOL, the compiler
that turns `entropy_engine.cob` into a working binary.

---

## Step 1: Check Your Windows Version

WSL2 requires **Windows 10 version 2004** (May 2020 update) or later, or
any version of Windows 11.

To check, open **PowerShell** and run:

```powershell
winver
```

A dialog will show your version. If you're below 2004, run Windows Update
before continuing.

---

## Step 2: Install WSL2 and Ubuntu

Open **PowerShell as Administrator** (right-click PowerShell in the Start
menu → *Run as administrator*) and run:

```powershell
wsl --install
```

This single command:
- Enables the WSL2 feature
- Downloads and installs Ubuntu
- Sets WSL2 as the default version

When Ubuntu first launches, it will ask you to create a **username** and
**password** for your Linux environment. Choose anything you like — you'll
need that password when running `sudo` commands.

> **Already have WSL installed?** Check which version you have:
> ```powershell
> wsl --list --verbose
> ```
> If any distro shows `VERSION 1`, upgrade it:
> ```powershell
> wsl --set-version Ubuntu 2
> ```

**Restart your computer** when prompted before moving on.

---

## Step 3: Open Ubuntu

After restarting, open **Ubuntu** from the Start menu (search for "Ubuntu").
A terminal window opens with a prompt that looks like:

```
yourname@DESKTOP-XXXXXXX:~$
```

Everything from here runs inside Ubuntu unless noted otherwise.

---

## Step 4: Update the Package List

Before installing anything, refresh Ubuntu's list of available software:

```bash
sudo apt update
```

Enter your Ubuntu password when prompted. This doesn't install anything —
it just makes sure you're about to install the latest versions.

---

## Step 5: Install Python

Ubuntu ships with Python 3, but let's make sure it's present and pip is
available:

```bash
sudo apt install python3 python3-pip -y
```

Verify the installation:

```bash
python3 --version
```

Expected output:

```
Python 3.12.x
```

> **Note:** Inside WSL, Python is invoked as `python3`. If you run the
> audit from a Windows terminal (PowerShell, Git Bash), the command is
> usually `python`. The project's README uses `python` throughout; swap
> in `python3` when running from inside WSL.

---

## Step 6: Install GnuCOBOL

GnuCOBOL is the compiler that turns `entropy_engine.cob` into a runnable
binary. Install it with:

```bash
sudo apt install gnucobol -y
```

Verify it worked:

```bash
cobc --version
```

Expected output:

```
cobc (GnuCOBOL) 3.1.2.0
Copyright (C) 2020 Free Software Foundation, Inc.
...
```

The exact version number may differ — anything 3.x is fine.

---

## Step 7: Navigate to the Project

Your Windows files are accessible from inside WSL under `/mnt/c/`.
Navigate to wherever you saved SilentSpace Guardian:

```bash
cd /mnt/c/Users/YourWindowsUsername/silentspace-guardian
```

Replace `YourWindowsUsername` with your actual Windows username. Not sure
what it is? List all Windows user directories:

```bash
ls /mnt/c/Users/
```

Confirm you're in the right place:

```bash
ls
```

You should see `README.md`, `cobol/`, `python/`, `meetings/`, and the
rest of the project files listed.

---

## Step 8: (Optional) Compile the COBOL Engine Manually

The audit script compiles the COBOL binary automatically on first run, so
this step is optional — but it's useful to understand what's happening:

```bash
cobc -x -o cobol/entropy_engine cobol/entropy_engine.cob
```

What each flag does:

| Flag | Meaning |
|---|---|
| `cobc` | Invoke the GnuCOBOL compiler |
| `-x` | Produce an executable binary (not a library) |
| `-o cobol/entropy_engine` | Name the output file `entropy_engine` |
| `cobol/entropy_engine.cob` | The COBOL source file to compile |

Success produces no output and creates a new file at `cobol/entropy_engine`.
You can verify it exists:

```bash
ls -lh cobol/entropy_engine
```

---

## Step 9: Run Your First Audit

```bash
python3 python/audit_meeting.py meetings/weekly_alignment_sync.json
```

If you skipped Step 8, the script detects that the binary is missing,
compiles it automatically, and then runs the audit. First-run output:

```
Compiling COBOL entropy engine...
Compilation successful.

==============================================================
  SilentSpace Guardian -- Meeting Audit
==============================================================
  Meeting  : Weekly Alignment Sync
  Waste    : 92/100
  Necessity: 8%
  Verdict  : Corporate Heat Death Event: Entropy Made Flesh — This meeting is why people quit.
  Async    : Declare a calendar emergency. Block this timeslot for silent, focused work.
==============================================================

  Report saved to: reports/weekly_alignment_sync_report.md
```

On every subsequent run, the binary already exists and compilation is skipped.

The generated report is saved to `reports/weekly_alignment_sync_report.md`.
You can open that file in Windows Explorer normally — it's a Markdown file
readable in VS Code, GitHub, or any text editor.

---

## Audit All 12 Meetings at Once

```bash
python3 python/audit_all_meetings.py
```

This scores every JSON file in `meetings/`, writes individual Markdown reports
to `reports/`, and produces a summary report at `reports/summary_report.md`
with aggregate statistics, verdict breakdown, top offenders, and most common
failure mode.

---

## Troubleshooting

### `cobc: command not found`

GnuCOBOL didn't install. Try reinstalling:

```bash
sudo apt update && sudo apt install gnucobol -y
```

### `python3: command not found`

```bash
sudo apt install python3 -y
```

### `cd: /mnt/c/...: No such file or directory`

Double-check your Windows username and path. List all available user
directories to find the right one:

```bash
ls /mnt/c/Users/
```

### `ModuleNotFoundError: No module named 'classify'`

You're running the script from the wrong directory. Make sure you're in
the project root — the folder that contains `README.md` — not inside `python/`:

```bash
pwd
# Should show: /mnt/c/Users/YourName/silentspace-guardian
```

### `Permission denied` when running `cobol/entropy_engine`

Mark the compiled binary as executable:

```bash
chmod +x cobol/entropy_engine
```

### The script says "Compiling via WSL" when run from Windows

That's expected. When you run `python audit_meeting.py` from a Windows
terminal (PowerShell, Git Bash, Command Prompt), the script detects that
native `cobc` isn't available and automatically delegates compilation to
WSL Ubuntu. You don't need to do anything — this is the intended behaviour.

---

*That's everything. The entropy engine is compiled, the corpus is loaded,
and your calendar's suffering can now be quantified.*
