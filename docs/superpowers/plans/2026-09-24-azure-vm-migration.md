# Azure VM migration implementation plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

Goal: Run the career platform on the Azure VM with the laptop's SQLite data, and confirm the site answers on the VM and shows that data.

Architecture: The app is cloned from GitHub into the azureuser home folder and installed with uv from the lock file. The laptop's database is copied into the checkout's `data/` folder, and Uvicorn serves it on `127.0.0.1:8000`. The site is checked on the VM with curl and from the laptop through an SSH tunnel, so no new port opens to the internet.

Tech stack: Ubuntu Server 24.04 LTS, Python 3.12, uv, FastAPI, Uvicorn, SQLAlchemy, Alembic, and SQLite.

Spec: Greg's migration plan from chat on 2026-09-24, copied here since it has no separate file.

```text
Server     Azure VM, already created, reached over SSH
Packages   apt-get: git, sqlite3
Code       git clone from GitHub
Python     uv, then uv sync from the lock file
Config     copy .env from .env.example
Data       scp my SQLite .db file from my laptop
Processes  start uvicorn
Verify     the site answers on the VM and shows my data
```

This is a first draft and is open to revisions. It's updated as each section runs, with a dated result line under every step.

Progress: All eight sections are done as of 2026-09-29, plus a content refresh that replaced the demo data with Greg's resume. Uvicorn listens on `0.0.0.0:8000`, and the rule `Temp-HTTP-8000` exposes it to the internet. The server won't restart after a reboot or deallocation until the systemd plan is done.

## Global constraints

- VM: `vm-career-platform` in resource group `rg-career-platform`.
- Public IP: static, and kept out of this file. Laptop commands read it from the `VM_IP` shell variable, which Server step 1 sets from Azure. Set it again in any new terminal before running a later section.
- SSH user: `azureuser`. SSH key: `~/.ssh/isba4775_azure`. Every SSH and scp command uses both.
- Repository: `https://github.com/lontok/career-platform.git`, branch `main`. It's public, so the clone needs no credentials.
- Checkout on the VM: `/home/azureuser/career-platform`.
- Database on the VM: `/home/azureuser/career-platform/data/resume.db`, matching `DATABASE_URL=sqlite:///./data/resume.db` in `.env.example`.
- Uvicorn binds to `127.0.0.1:8000` only. No network security group rule opens port 8000.
- Never run `uv run python -m app.seed` on the VM. The seed writes the demo profile "Alex Parker" and would overwrite the migrated records.
- Every `uv run` on the VM includes `--no-dev`. A plain `uv run` installs the dev group, pytest and ruff, back into `.venv`.
- Never commit `.env` or any `.db` file.
- Laptop commands run from the repo root on the laptop.

## Review focus

These five conditions aren't covered by the spec, and they're the most likely to break the migration. Each one has a check in the step that owns it.

1. Someone runs the seed out of habit because the README's local setup includes it. The migrated data gets replaced with demo records. Data step 4 says not to seed, and Verify step 2 compares the VM database's SHA-256 hash with the laptop copy's. The laptop data is itself the seed's demo profile, "Alex Parker," so a name check can't catch a seed run, but any write changes the hash.
2. Uvicorn starts from a folder other than the repo root. The relative database path then points at a new, empty file, and the site renders without your data. Processes step 1 starts from the repo root, and Verify step 2 checks for your profile name.
3. The laptop's public IP has changed since the SSH rule was written. SSH then times out instead of refusing. Server steps 2 and 3 compare the rule's source address with the current IP.
4. The laptop database changes while it's being copied, or its WAL file never reaches the VM. The VM would then get a stale or partial copy. Data step 1 copies it with the repo's backup script, which takes a consistent snapshot and runs an integrity check.
5. The scp lands on top of an existing database on the VM. Data step 2 confirms the target doesn't exist before anything is copied.

---

## 1. Server

- [x] Step 1: Confirm the VM is running and has the expected IP, and start it if it's stopped.
  - Runs on: laptop.
  - Do:

    ```bash
    az vm show -d -g rg-career-platform -n vm-career-platform \
      --query "{state:powerState, ip:publicIps, size:hardwareProfile.vmSize}" -o json
    VM_IP=$(az vm show -d -g rg-career-platform -n vm-career-platform --query publicIps -o tsv)
    ```

    If `state` is `VM deallocated` or `VM stopped`, start it and run the check again:

    ```bash
    az vm start -g rg-career-platform -n vm-career-platform -o none
    ```

  - Why: Every later step assumes this VM and this address. A stopped VM or a changed IP would look like an SSH failure. The public IP is static, so starting the VM keeps the same address.
  - Check: `state` is `VM running`, `ip` isn't empty, and `echo "$VM_IP"` prints the same address.
  - Undo: If you started the VM here, stop billing for compute with `az vm deallocate -g rg-career-platform -n vm-career-platform`.
  - Result, 2026-09-29: The VM was deallocated. It started with `az vm start` and came back as `VM running` on the same static public IP, size `Standard_B2ts_v2`.

- [x] Step 2: Compare the SSH rule with the laptop's current public IP.
  - Runs on: laptop.
  - Do:

    ```bash
    LAPTOP_IP=$(curl -4 -s https://api.ipify.org) && echo "$LAPTOP_IP"
    NSG_ID=$(az network nic show --ids "$(az vm show -g rg-career-platform -n vm-career-platform \
      --query 'networkProfile.networkInterfaces[0].id' -o tsv)" --query networkSecurityGroup.id -o tsv)
    az network nsg show --ids "$NSG_ID" \
      --query "securityRules[].{name:name, port:destinationPortRange, source:sourceAddressPrefix, access:access}" -o table
    ```

  - Why: The IP can change when the laptop switches networks. If the rule allows port 22 only from an old address, SSH will time out.
  - Check: A rule allows port 22 with a source of `Any` or the IP the first command printed. If that's true, skip step 3.
  - Undo: Nothing to undo. This step only reads.
  - Result, 2026-09-29: The network security group `vm-career-platform-nsg` has one inbound rule, `Allow-SSH-Laptop`, which allows port 22 from a single `/32` address at priority 300. That address matched the laptop's current public IP, so step 3 was skipped.

- [x] Step 3: Add or fix the SSH rule, only if step 2 found no match.
  - Runs on: portal.
  - Do: Open Virtual machines, then vm-career-platform, then Networking, then Network settings. Click Create port rule, then Inbound port rule. Set Source to IP Addresses, Source IP addresses to the laptop IP followed by `/32`, Destination port ranges to `22`, Protocol to TCP, Action to Allow, and Name to `AllowSSH-laptop`. Click Add.
  - Why: SSH is the only way the rest of the plan reaches the VM. Limiting the rule to one address keeps port 22 closed to everyone else.
  - Check: The rule appears in the inbound list, and step 4 connects.
  - Undo: On the same page, select `AllowSSH-laptop` and click Delete.
  - Result, 2026-09-29: Skipped, because step 2 found a matching rule.

- [x] Step 4: Connect over SSH and check the VM's basics.
  - Runs on: laptop.
  - Do: On a first connection, compare the host key Azure reports with the one the network presents:

    ```bash
    az vm run-command invoke -g rg-career-platform -n vm-career-platform --command-id RunShellScript \
      --scripts "ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub" --query "value[0].message" -o tsv | grep SHA256
    ssh-keyscan -t ed25519 -T 10 "$VM_IP" 2>/dev/null | ssh-keygen -lf -
    ```

    If the two fingerprints match, connect:

    ```bash
    ssh -i ~/.ssh/isba4775_azure -o StrictHostKeyChecking=accept-new azureuser@"$VM_IP" \
      'hostname && lsb_release -ds && free -m | head -2 && df -h ~ | tail -1'
    ```

  - Why: This proves the key, user, and firewall rule all work before anything is installed. It also shows the free memory and disk before the install uses them. The fingerprint comparison uses Azure's own view of the VM, so a different machine answering on that IP would show up as a mismatch.
  - Check: The fingerprints match. The output shows `vm-career-platform`, `Ubuntu 24.04`, about 840 MiB of total memory, and several GB free on the disk. A 1 GiB size shows less than 1 GiB because Azure and the kernel reserve part of it.
  - Undo: Remove the saved host key with `ssh-keygen -R "$VM_IP"`.
  - Result, 2026-09-29: The two ED25519 fingerprints matched, and `known_hosts` already held that key. SSH printed `vm-career-platform` and `Ubuntu 24.04.4 LTS`. Memory showed 841 MiB total with 432 MiB available, and the disk had 27 GB free of 29 GB. The low memory matters most in Python step 2, where uv installs the dependencies.

## 2. Packages

Each VM step from here on runs inside an SSH session opened with this command:

```bash
ssh -i ~/.ssh/isba4775_azure azureuser@"$VM_IP"
```

- [x] Step 1: Record which packages are already installed.
  - Runs on: VM.
  - Do:

    ```bash
    for p in git sqlite3; do dpkg -s "$p" >/dev/null 2>&1 && echo "$p already installed" || echo "$p missing"; done
    ```

  - Why: Ubuntu images usually ship with git. Writing down what was already there keeps the undo step from removing something the system needs.
  - Check: Each package prints one line. Note which ones say missing.
  - Undo: Nothing to undo. This step only reads.
  - Result, 2026-09-29: git was already installed. sqlite3 was missing.

- [x] Step 2: Install git and sqlite3.
  - Runs on: VM.
  - Do:

    ```bash
    sudo apt-get update
    sudo apt-get install -y git sqlite3
    ```

  - Why: git clones the code, and sqlite3 checks the copied database and runs the counts in the Data and Verify steps.
  - Check:

    ```bash
    git --version && sqlite3 --version
    ```

    Both print a version number.
  - Undo: Remove only the packages step 1 listed as missing, for example `sudo apt-get remove -y sqlite3`.
  - Result, 2026-09-29: apt installed only `sqlite3` 3.45.1-1ubuntu2.8, confirmed in `/var/log/dpkg.log`. git stayed at 2.43.0 and sqlite3 reports 3.45.1. The undo for this VM is `sudo apt-get remove -y sqlite3`, and git stays.

## 3. Code

- [x] Step 1: Note the commit the laptop expects.
  - Runs on: laptop.
  - Do:

    ```bash
    git fetch origin && git status -sb | head -1 && git log -1 --oneline origin/main
    ```

  - Why: The VM clones from GitHub, not from the laptop. Local commits that were never pushed won't reach the VM.
  - Check: The status line shows `main...origin/main` with no "ahead." Write down the short commit ID. It was `52eee06` when this plan was written.
  - Undo: Nothing to undo. This step only reads.
  - Result, 2026-09-29: The laptop showed `main...origin/main` with nothing ahead, and both `HEAD` and `origin/main` were `52eee06`. The only local change was this plan file, which is untracked and isn't needed on the VM.

- [x] Step 2: Clone the repository.
  - Runs on: VM.
  - Do:

    ```bash
    git clone https://github.com/lontok/career-platform.git ~/career-platform
    ```

  - Why: This gives the VM the same code and the same `uv.lock` the laptop uses.
  - Check:

    ```bash
    git -C ~/career-platform log -1 --oneline
    ```

    The commit ID matches the one from step 1.
  - Undo: `rm -rf ~/career-platform`. After the Data section has run, copy `data/resume.db` somewhere else first.
  - Result, 2026-09-29: A check that `~/career-platform` didn't exist ran first, then the clone. The VM's checkout is on `52eee06` and tracks `origin/main`, matching the laptop.

## 4. Python

- [x] Step 1: Install uv.
  - Runs on: VM.
  - Do:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
    ```

  - Why: The project pins its dependencies in `uv.lock`, and uv is the tool that reads it. The installer puts uv in `~/.local/bin` and doesn't need sudo.
  - Check:

    ```bash
    uv --version
    ```

    It prints a version number.
  - Undo:

    ```bash
    rm -f ~/.local/bin/uv ~/.local/bin/uvx
    rm -rf ~/.local/share/uv ~/.cache/uv
    ```

    Then delete the line that sources `$HOME/.local/bin/env` from `~/.bashrc` and `~/.profile`.
  - Result, 2026-09-29: The installer put uv 0.12.21 at `/home/azureuser/.local/bin/uv`. It added `. "$HOME/.local/bin/env"` to line 119 of `~/.bashrc` and line 29 of `~/.profile`, which are the lines the undo removes.

- [x] Step 2: Install the locked dependencies.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    uv sync --locked --no-dev
    ```

  - Why: `--locked` stops with an error if `uv.lock` and `pyproject.toml` disagree, instead of quietly picking new versions. `--no-dev` skips pytest and ruff, which the server doesn't need.
  - Check:

    ```bash
    uv run --no-dev python --version
    uv run --no-dev python -c "import fastapi, uvicorn, sqlalchemy, alembic; print('imports ok')"
    ls .venv/bin | grep -E '^(ruff|pytest)$' || echo "no dev tools in .venv"
    ```

    The first prints Python 3.12, the second prints `imports ok`, and the third prints `no dev tools in .venv`.
  - Undo: `rm -rf ~/career-platform/.venv`. If uv downloaded its own Python, also run `uv python uninstall 3.12`.
  - Result, 2026-09-29: `uv sync --locked --no-dev` finished in under a second with a peak memory of about 87 MB, and the kernel logged no out-of-memory events. The first check ran as a plain `uv run`, which quietly installed the dev group, including pytest and ruff. The fix was to run `uv sync --locked --no-dev` again, which removed them, and to add `--no-dev` to every `uv run` in this plan. The rerun checks printed Python 3.12.3 and `imports ok`, and `.venv` had no dev tools. uv used Ubuntu's `/usr/bin/python3.12` and downloaded no Python of its own, so the undo only needs to remove `.venv`.

## 5. Config

- [x] Step 1: Create `.env` from the example.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    cp --update=none .env.example .env
    chmod 600 .env
    ```

  - Why: The app's settings read `.env` from the folder it starts in. The example's `DATABASE_URL=sqlite:///./data/resume.db` points at the file the Data section copies. `--update=none` keeps an existing `.env` from being overwritten.
  - Check:

    ```bash
    uv run --no-dev python -c "from app.core.config import Settings; print(Settings().database_url)"
    ```

    It prints `sqlite:///./data/resume.db`.
  - Undo: `rm ~/career-platform/.env`.
  - Result, 2026-09-29: No `.env` existed before this step. The file came out with mode `600`, owned by azureuser, containing only `DATABASE_URL=sqlite:///./data/resume.db`. The settings check printed that same URL, and git reports `.env` as ignored. The run used `cp -n`, which printed a warning that `-n` may change in future coreutils, so the command above now uses `--update=none`, which does the same thing.

The comment in `.env.example` says production settings belong in `/etc/career-platform/environment`. That's the full runbook in `deploy/README.md`, which this plan doesn't cover yet. For this first move, `.env` in the checkout is enough.

## 6. Data

- [x] Step 1: Make a checked copy of the laptop database and record its row counts.
  - Runs on: laptop.
  - Do: Stop any local Uvicorn serving this repo first, so nothing writes to the database during the copy. `lsof data/resume.db` should print nothing. Then run:

    ```bash
    BACKUP_FILE=$(bash deploy/scripts/backup-sqlite.sh data/resume.db data/migration-copy)
    echo "$BACKUP_FILE"
    sqlite3 "$BACKUP_FILE" "SELECT 'profiles', COUNT(*) FROM profiles UNION ALL SELECT 'experiences', COUNT(*) FROM experiences UNION ALL SELECT 'projects', COUNT(*) FROM projects UNION ALL SELECT 'skills', COUNT(*) FROM skills UNION ALL SELECT 'education', COUNT(*) FROM education;"
    sqlite3 "$BACKUP_FILE" "SELECT full_name FROM profiles;"
    shasum -a 256 "$BACKUP_FILE"
    ```

  - Why: The backup script takes a consistent snapshot with SQLite's own backup command and fails if the integrity check doesn't return `ok`. Copying the raw file could miss changes still sitting in a WAL file.
  - Check: The script prints a path ending in `.db`. Write down the five counts and the hash, since Data steps 3 and 4 and Verify step 2 compare against them.
  - Undo: `rm -r data/migration-copy`.
  - Result, 2026-09-29: A Uvicorn process was running on port 8000, but its working folder was a different project and `lsof` showed nothing holding `data/resume.db`, so it was left alone. The copy is `data/migration-copy/resume-20260929T214102Z-95602.db`, 126,976 bytes, and passed the integrity check. Counts were profiles 1, experiences 1, projects 1, skills 2, and education 1. The Alembic version was `20260917_02`. The profile name was `Alex Parker`, which means the laptop still holds the seed's demo content, not personal resume content. The SHA-256 hash was `c613bc161ebda9c47525e65f1258cb632d6abdef3162e31a7da044d1fb24453c`.

- [x] Step 2: Confirm the target on the VM is empty.
  - Runs on: VM.
  - Do:

    ```bash
    mkdir -p ~/career-platform/data
    test ! -e ~/career-platform/data/resume.db && echo "target is free"
    ```

  - Why: scp overwrites without asking. If a database already exists there, stop and decide what to do with it before copying.
  - Check: It prints `target is free`. If it prints nothing, stop here.
  - Undo: The repo doesn't track `data/`, so `mkdir` creates it. Remove it with `rmdir ~/career-platform/data` while it's still empty.
  - Result, 2026-09-29: It printed `target is free`, and `data/` was empty.

- [x] Step 3: Copy the database to the VM.
  - Runs on: laptop, in the same terminal as step 1 so `BACKUP_FILE` is still set.
  - Do:

    ```bash
    scp -i ~/.ssh/isba4775_azure "$BACKUP_FILE" azureuser@"$VM_IP":career-platform/data/resume.db
    shasum -a 256 "$BACKUP_FILE"
    ssh -i ~/.ssh/isba4775_azure azureuser@"$VM_IP" 'sha256sum ~/career-platform/data/resume.db'
    ```

  - Why: This is the only copy of your resume data outside the laptop. The app on the VM reads it from this path.
  - Check: scp finishes without an error, and the two hashes match. Step 4 checks the contents.
  - Undo:

    ```bash
    ssh -i ~/.ssh/isba4775_azure azureuser@"$VM_IP" 'rm ~/career-platform/data/resume.db'
    ```

  - Result, 2026-09-29: scp succeeded, and both sides hashed to `c613bc161ebda9c47525e65f1258cb632d6abdef3162e31a7da044d1fb24453c`.

- [x] Step 4: Check the copy on the VM, and don't seed.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    chmod 600 data/resume.db
    sqlite3 data/resume.db "PRAGMA integrity_check;"
    sqlite3 data/resume.db "SELECT 'profiles', COUNT(*) FROM profiles UNION ALL SELECT 'experiences', COUNT(*) FROM experiences UNION ALL SELECT 'projects', COUNT(*) FROM projects UNION ALL SELECT 'skills', COUNT(*) FROM skills UNION ALL SELECT 'education', COUNT(*) FROM education;"
    uv run --no-dev alembic current
    uv run --no-dev alembic heads
    sha256sum data/resume.db
    ```

  - Why: The integrity check and counts prove the file arrived whole. The two Alembic commands show whether the database schema matches the code, since a mismatch would break pages at runtime.
  - Check: The integrity check prints `ok`. The counts match the laptop's from step 1. `alembic current` shows the same revision as `alembic heads`, marked `(head)`. If current is behind, stop and back up the file with `deploy/scripts/backup-sqlite.sh` before running `uv run --no-dev alembic upgrade head`. Do not run `app.seed`. The hash still matches step 3, which shows the checks didn't write to the file.
  - Undo: Same as step 3.
  - Result, 2026-09-29: The file is mode `600`, owned by azureuser. The integrity check printed `ok`, and the counts matched the laptop's. Both `alembic current` and `alembic heads` printed `20260917_02 (head)`, so no migration was needed. The hash after the checks was still `c613bc161ebda9c47525e65f1258cb632d6abdef3162e31a7da044d1fb24453c`. The seed wasn't run.

## 7. Processes

- [x] Step 1: Start Uvicorn in the background from the repo root.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    nohup uv run --no-dev uvicorn app.main:app --host 127.0.0.1 --port 8000 > ~/uvicorn.log 2>&1 < /dev/null &
    echo $! > ~/uvicorn.pid
    ```

  - Why: Starting in `~/career-platform` makes the relative database path resolve to the copied file. `nohup` keeps the server running after the SSH session closes, and `< /dev/null` stops a one-line `ssh` command from waiting on the background process. Binding to `127.0.0.1` matches the runbook and keeps port 8000 off the internet.
  - Check:

    ```bash
    sleep 3
    tail -5 ~/uvicorn.log
    ss -ltn | grep ':8000'
    ```

    The log shows `Uvicorn running on http://127.0.0.1:8000`, and `ss` shows a listener on `127.0.0.1:8000` and nowhere else.
  - Undo:

    ```bash
    kill "$(cat ~/uvicorn.pid)" || pkill -f "uvicorn app.main:app"
    rm -f ~/uvicorn.pid
    ```

  - Result, 2026-09-29: Neither `pgrep -fa "uvicorn app.main:app"` nor `ss` found anything on port 8000 beforehand. A pre-check sent inline as `ssh host '...'` matched its own command line, so the script went through `ssh host bash -s` with a heredoc instead. After start, the log showed `Uvicorn running on http://127.0.0.1:8000`, and `ss` showed a single listener on `127.0.0.1:8000`. The pidfile holds 13504, the `uv run` parent, and Uvicorn itself is 13508. A new SSH session showed both still running with the parent reparented to PID 1, so the server outlived the session that started it. `.venv` still has no dev tools.

Change, 2026-09-29, at Greg's request: Uvicorn was restarted with `--host 0.0.0.0 --port 8000`, so it listens on every address. The pidfile now holds 13847, and Uvicorn itself is 13851. `ss -ltnp` shows `0.0.0.0:8000`, and `/health` answers on `127.0.0.1` and on the VM's private IP. The network security group now also has `Temp-HTTP-8000`, which allows port 8000 from any source at priority 310. That rule wasn't created by this plan, and it makes the app reachable at port 8000 on the VM's public IP from the internet. Both changes depart from the Global constraints, which call for `127.0.0.1` only and no rule for port 8000. To go back, restart with `--host 127.0.0.1` and delete `Temp-HTTP-8000`.

This process doesn't restart after a reboot. The systemd unit in `deploy/systemd/career-platform.service` handles that, but it expects the `/srv` layout from the full runbook, so it's left for a later plan.

## 8. Verify

- [x] Step 1: Check the health endpoint on the VM.
  - Runs on: VM.
  - Do:

    ```bash
    curl --fail http://127.0.0.1:8000/health && echo
    ```

  - Why: This confirms the app loaded and is answering before any page reads the database.
  - Check: It prints `{"status":"ok"}`.
  - Undo: Nothing to undo. This step only reads.
  - Result, 2026-09-29: It printed `{"status":"ok"}`.

- [x] Step 2: Check that the pages answer and show your data.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    for p in / /experience /projects /skills /education /projects/career-platform /projects/does-not-exist; do
      curl -s -o /dev/null -w "%{http_code} $p\n" "http://127.0.0.1:8000$p"
    done
    PROFILE_NAME=$(sqlite3 data/resume.db "SELECT full_name FROM profiles LIMIT 1;")
    echo "$PROFILE_NAME"
    curl -s http://127.0.0.1:8000/ | grep -c "$PROFILE_NAME"
    sha256sum data/resume.db
    ```

  - Why: A 200 on every page shows the routes work. Finding the database's profile name on the home page shows the app is reading the migrated file and not an empty one. The hash shows nothing, including an accidental seed, has written to the file since it was copied.
  - Check: Every page prints `200` except `/projects/does-not-exist`, which prints `404`. The name matches the one from Data step 1, and the count is at least `1`. The hash is still `c613bc161ebda9c47525e65f1258cb632d6abdef3162e31a7da044d1fb24453c`. If it differs, something wrote to the database, and the data needs to be copied again.
  - Undo: Nothing to undo. This step only reads.
  - Result, 2026-09-29: The five main pages and `/projects/career-platform` returned `200`, and the made-up project returned `404`, as the README's release checklist expects. The name was `Alex Parker`, the migrated demo profile, and it appeared twice on the home page, in the title and the `h1`. The hash was still `c613bc161ebda9c47525e65f1258cb632d6abdef3162e31a7da044d1fb24453c`. `~/uvicorn.log` had no errors or tracebacks.

- [x] Step 3: View the site from the laptop through an SSH tunnel.
  - Runs on: laptop.
  - Do:

    ```bash
    ssh -i ~/.ssh/isba4775_azure -N -L 8001:127.0.0.1:8000 azureuser@"$VM_IP"
    ```

    Leave it running, then open http://localhost:8001 in a browser.
  - Why: The tunnel shows the real pages without opening a port on the VM. Local port 8001 avoids a clash with a local server on 8000.
  - Check: The home, experience, projects, skills, and education pages show your records.
  - Undo: Press Ctrl+C in the tunnel's terminal.
  - Result, 2026-09-29: Port 8001 on the laptop was free. The tunnel ran in the background with `ssh -f -N -o ExitOnForwardFailure=yes`, and the five main pages returned `200` through `http://localhost:8001`. The home page title was `Alex Parker | Career Platform`, and the skills page listed SQL and Python. The tunnel was then closed with `pkill`, and port 8001 was free again. Afterward the VM database hash was unchanged and Uvicorn was still running. This check used curl, so a visual look in a browser is still open for Greg.

## Content refresh, 2026-09-29

Greg's resume replaced the demo content in commit `d8179a1`. The seed never runs on the VM, so the laptop database was re-seeded and copied over. Data step 2 refuses to overwrite an existing database, so the old VM file was moved aside first.

- [x] Step 1: Re-seed the laptop database and make a checked copy.
  - Runs on: laptop.
  - Do:

    ```bash
    bash deploy/scripts/backup-sqlite.sh data/resume.db data/backups
    uv run alembic upgrade head
    uv run python -m app.seed
    BACKUP_FILE=$(bash deploy/scripts/backup-sqlite.sh data/resume.db data/migration-copy)
    shasum -a 256 "$BACKUP_FILE"
    ```

  - Why: The first backup keeps the pre-seed file. The seed writes the new content, and the second backup is the checked copy that goes to the VM.
  - Check: The seed prints `Seeded published resume content.`, and the integrity checks inside both backups pass.
  - Undo: Restore the pre-seed backup with `deploy/scripts/restore-sqlite.sh` into a new file, then swap it in.
  - Result, 2026-09-29: The pre-seed backup is `data/backups/resume-20260929T221608Z-63620.db`. After the seed, the database published 1 profile, 7 experiences, 1 project, 4 skills, and 2 education records. The replaced demo rows stay in the file as unpublished. The copy is `data/migration-copy/resume-20260929T221650Z-65448.db`, hash `44b8fe5dd575d1db33d40d57860ef8f81f771ddead644b55cc50ce8f6714a5f7`.

- [x] Step 2: Back up the VM database, stop the app, pull the code, and set the old file aside.
  - Runs on: VM.
  - Do:

    ```bash
    cd ~/career-platform
    bash deploy/scripts/backup-sqlite.sh data/resume.db ~/career-platform-backups
    kill "$(cat ~/uvicorn.pid)"
    git pull --ff-only
    mv data/resume.db "data/resume.pre-profile-$(date -u +%Y%m%dT%H%M%SZ).db"
    test ! -e data/resume.db && echo "target is free"
    ```

  - Why: The template changes that hide empty fields only reach the VM through GitHub. Moving the old file keeps it on disk while freeing the path for the copy.
  - Check: `pgrep -fa "uvicorn app.main:app"` prints nothing, `git log -1` shows `d8179a1`, and the last command prints `target is free`.
  - Undo: `git checkout 52eee06`, then move the `resume.pre-profile-*` file back to `data/resume.db`.
  - Result, 2026-09-29: The backup is `~/career-platform-backups/resume-20260929T221658Z-14056.db`. The old file is `data/resume.pre-profile-20260929T221700Z.db`, and the checkout is on `d8179a1`.

- [x] Step 3: Copy the new database, check it, and restart.
  - Runs on: laptop, then VM.
  - Do: Run Data steps 3 and 4 with the new `BACKUP_FILE`. Then start Uvicorn as in Processes step 1, using `--host 0.0.0.0` to match the current setup.
  - Why: This is the same checked path as the first migration, so the same hash, integrity, and schema checks apply.
  - Check: The hashes match, the integrity check prints `ok`, and `alembic current` equals `alembic heads`. Every page returns `200`, the home page `h1` is `Greg Lontok`, and neither "Alex Parker" nor "Target roles" appears.
  - Undo: Stop Uvicorn, move the `resume.pre-profile-*` file back, and start it again.
  - Result, 2026-09-29: Both sides hashed to `44b8fe5dd575d1db33d40d57860ef8f81f771ddead644b55cc50ce8f6714a5f7`, and the hash was unchanged after the pages loaded. The file published 7 experiences, 2 education records, and 4 skills, and the schema was at `20260917_02 (head)`. Uvicorn listens on `0.0.0.0:8000`. The home, experience, projects, project detail, skills, education, and health pages all returned `200`, including from the laptop over the public IP.

## Rolling back the whole migration

Run the undo steps in reverse order: Verify, Processes, Data, Config, Python, Code, Packages, and Server. The laptop database is never changed by this plan, so it stays the source of truth throughout.

## Out of scope

Nginx, HTTPS, the dedicated service account, the systemd unit, the `/srv` and `/var/lib` layout, and ports 80 and 443 are all in `deploy/README.md`. They'd be the next plan once this first move works.
