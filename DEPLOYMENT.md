# Deployment & Operations Runbook

This is the single source of truth for deploying and running the Automated Tax Rulings
Scraper — written so that **someone with no prior server or Coolify experience** can follow
it end-to-end. Every step says exactly what to click or type. If you already have the server
and Coolify running, skip ahead to the section you need using the list below.

## Contents

1. [What this application does](#1-what-this-application-does)
2. [What you need before you start](#2-what-you-need-before-you-start)
3. [Part A — Get a server](#part-a--get-a-server)
4. [Part B — Install Coolify on the server](#part-b--install-coolify-on-the-server)
5. [Part C — First-time Coolify setup](#part-c--first-time-coolify-setup)
6. [Part D — Create the project and connect the GitHub repo](#part-d--create-the-project-and-connect-the-github-repo)
7. [Part E — Set the build method to Dockerfile](#part-e--set-the-build-method-to-dockerfile)
8. [Part F — Set up the email account (sending daily summaries)](#part-f--set-up-the-email-account-sending-daily-summaries)
9. [Part G — Set up FTP file storage](#part-g--set-up-ftp-file-storage)
10. [Part H — Set up the Google Sheet and Google service account](#part-h--set-up-the-google-sheet-and-google-service-account)
11. [Part I — Add all the environment variables](#part-i--add-all-the-environment-variables)
12. [Part J — Upload the Google service-account credentials file](#part-j--upload-the-google-service-account-credentials-file)
13. [Part K — Deploy the app for the first time](#part-k--deploy-the-app-for-the-first-time)
14. [Part L — Set up the daily Scheduled Task](#part-l--set-up-the-daily-scheduled-task)
15. [Part M — Test that everything works](#part-m--test-that-everything-works)
16. [Quick reference](#16-quick-reference)

---

## 1. What this application does

In plain terms: every morning, a small program wakes up, logs into two websites
(Taxsutra.com and Taxmann.com), copies the tax rulings/updates published that
day, saves them into a Google Sheet, emails a summary to a list of people, and
uploads the downloaded PDF files to a web server via FTP so they're accessible
online. It then goes back to sleep until the next day.

It runs inside a small piece of software called a **container** (think of it as
a sealed, self-contained mini-computer that only has exactly what this app
needs installed in it), hosted on a server you control, managed by a tool
called **Coolify** (a web dashboard for deploying and scheduling apps on your
own server — an alternative to paying for a service like Heroku).

## 2. What you need before you start

Gather these before doing anything else:

- [ ] A server you can install software on (see Part A if you don't have one yet)
- [ ] Access to the GitHub repository: `git@github-shreyansmaloo:shreyansmaloo/automated-tax-rulings-scraper.git`
      (ask the repo owner to add you as a collaborator, or ask for a copy of the code)
- [ ] A Taxsutra.com login (username + password) with an active subscription
- [ ] A Taxmann.com login (email + password) with an active subscription
- [ ] An email account to send the daily summary from (Part F)
- [ ] An FTP account to receive the downloaded PDF files (Part G)
- [ ] A Google Sheet + Google service account to store the scraped data (Part H)

None of the real passwords/keys ever go into this document or into the GitHub
repository — they only ever get typed into Coolify's own settings screens,
which is explained step by step below.

---

## Part A — Get a server

You need one Linux server (a "VPS" — Virtual Private Server) that is always
on and reachable over the internet. Coolify and this app will both run on it.

**Minimum specs**: 2 CPU cores, 4 GB RAM, 40 GB disk, Ubuntu 22.04 or 24.04.
(Chrome/Chromium, which this app drives to do the scraping, needs a decent
amount of memory — going below 4 GB RAM risks the browser crashing mid-run.)

**Example using Hostinger** (any VPS provider works the same way in spirit —
DigitalOcean, Linode, Hetzner, AWS Lightsail, etc.):

1. Go to Hostinger → **VPS Hosting** → choose a plan meeting the specs above.
2. During setup, pick **Ubuntu 22.04** (or 24.04) as the operating system —
   choose the plain OS template, not one of the pre-installed app templates.
3. Once it's provisioned, Hostinger will show you the server's **IP address**
   and a **root password** (or you can upload your own SSH key during setup —
   recommended if you know how, otherwise the password is fine to start).
4. From your own computer, open a terminal and connect to the server:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
   Type `yes` if asked to confirm the connection, then enter the password
   Hostinger gave you. You're now "inside" the server.

Keep that IP address handy — you'll use it for the rest of this guide.

---

## Part B — Install Coolify on the server

While connected to the server via SSH (see Part A, step 4), run Coolify's
official installer:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

This downloads and sets up Coolify and everything it needs (Docker, etc.)
automatically. It takes a few minutes. When it finishes, it will print a URL
that looks like:

```
http://YOUR_SERVER_IP:8000
```

That's your Coolify dashboard address — keep it, you'll use it constantly.

---

## Part C — First-time Coolify setup

1. Open `http://YOUR_SERVER_IP:8000` in your web browser.
2. The first time, Coolify asks you to **create an admin account** (your own
   email + a password you choose). This is a local account just for your
   Coolify dashboard — it has nothing to do with Taxsutra/Taxmann/Google/etc.
3. Log in. You'll land on the Coolify **Dashboard**.

*(For this project specifically, the existing dashboard is already running at
`http://91.108.104.17:8000` — ask the current admin for an invite instead of
setting up a brand-new one, unless you're deliberately standing up a second,
separate deployment.)*

---

## Part D — Create the project and connect the GitHub repo

1. In Coolify's left sidebar, click **Projects → + Add** (or use an existing
   project if one's already set up — this app currently lives under a
   project called **Tax Scraper**, environment **production**).
2. Inside the project, click **+ Add Resource**.
3. Choose **Application**, then choose **Public/Private Git Repository**.
4. If this is the first time connecting to this GitHub account, Coolify will
   ask you to connect a **Source** — either:
   - **GitHub App integration** (recommended): click "Connect to GitHub",
     authorize Coolify, and pick the `automated-tax-rulings-scraper`
     repository from the list. This lets Coolify auto-detect new commits.
   - **Or** paste the repository URL directly
     (`git@github-shreyansmaloo:shreyansmaloo/automated-tax-rulings-scraper.git`)
     and add an SSH deploy key if the repo is private and you're not using
     the GitHub App method.
5. Pick the **`main`** branch.
6. Give the application a name (e.g. `automated-tax-rulings-scraper`) and
   finish creating it.

You'll now be looking at the application's **Configuration** page — this is
where almost everything else in this guide happens.

---

## Part E — Set the build method to Dockerfile

1. On the application's **Configuration → General** tab, find the
   **Build Pack** dropdown.
2. Set it to **Dockerfile**.

This tells Coolify to build the app using the `Dockerfile` already included
in the repository, instead of trying to auto-detect how to build it. This
specific choice matters a lot for this app — the repo also contains a
`nixpacks.toml` file, but it should **not** be used (leave Build Pack on
Dockerfile). The short version of why: Coolify's alternative build method
(Nixpacks) builds on Ubuntu, and Ubuntu's version of the Chrome browser
package doesn't actually work inside a plain container — it's a shortcut that
expects a feature (`snap`) that isn't there. The `Dockerfile` in this repo
uses a different base (Debian) whose Chrome package works correctly out of
the box. Just leave Build Pack on **Dockerfile** and you won't need to think
about this again.

---

## Part F — Set up the email account (sending daily summaries)

The app sends its daily summary from a real email inbox using a password.
This project currently uses an **Outlook / Microsoft 365** account. Here's
how to get the two values you'll need (`EMAIL_SENDER` and `EMAIL_PASSWORD`)
for a Microsoft account:

1. Decide which email address will send the daily summary (it can be an
   existing Outlook/Office365 mailbox, or a new free one you create at
   [outlook.com](https://outlook.com)). This full address is your
   `EMAIL_SENDER` value.
2. Go to [https://account.microsoft.com/security](https://account.microsoft.com/security)
   and sign in as that email account.
3. Microsoft requires **two-step verification (2FA)** to be turned on before
   it will let you create an "app password". If it's not already on, turn it
   on under **Advanced security options**.
4. On the same **Advanced security options** page, find **App passwords**
   and click **Create a new app password**.
5. Give it a name like `Tax Scraper` and click Create. Microsoft will show
   you a randomly generated password **once** — copy it immediately. This is
   your `EMAIL_PASSWORD` value (not your normal Outlook login password).
6. Keep both values (the email address and this app password) ready to paste
   into Coolify in Part I.

*(If you'd rather use Gmail instead of Outlook, the equivalent is
`myaccount.google.com/security` → turn on 2-Step Verification → App
passwords → generate one for "Mail". Then set
`EMAIL_SMTP_SERVER=smtp.gmail.com` and `EMAIL_SMTP_PORT=465` instead of the
Outlook values.)*

You'll also decide who receives the daily email — any number of addresses,
comma-separated, for `EMAIL_RECIPIENT`, and optionally BCC addresses for
`EMAIL_BCC`.

---

## Part G — Set up FTP file storage

The app uploads the PDF files it downloads to a web server over FTP, so they
end up somewhere accessible by a URL. This project currently uses
**Hostinger** hosting for this. Here's how to set up an FTP account on
Hostinger (or find the same settings if one already exists):

1. Log into **Hostinger hPanel** for the hosting account/website you want
   the files to end up on.
2. Go to **Files → FTP Accounts**.
3. Either use the **main FTP account** shown there, or click **Create FTP
   Account** to make a dedicated one just for this app (recommended, so it's
   easy to revoke later without affecting anything else).
4. When creating one, Hostinger asks for:
   - A **username** (this becomes your `FTP_USER`)
   - A **password** you choose (this becomes your `FTP_PASS`)
   - A **directory** this account is allowed to access — e.g.
     `public_html/data_scraper/rulings` (this becomes your `REMOTE_DIR`,
     written *relative to* the FTP account's own root — check Hostinger's
     "Directory" column to see the exact relative path it expects)
5. Hostinger shows the **FTP hostname or server IP** on the same page — this
   is your `FTP_HOST`. The **port** is almost always `21` (`FTP_PORT=21`).
6. Figure out the **public URL** for that same directory — since Hostinger
   serves anything under `public_html` on the website's domain, if you
   picked `public_html/data_scraper/rulings` as the FTP directory, the
   public URL is something like
   `https://your-domain.com/data_scraper/rulings/`. This becomes your
   `FILE_SERVER_URL` (used only for reference links in the summary email,
   not for the upload itself).

Keep `FTP_HOST`, `FTP_PORT`, `FTP_USER`, `FTP_PASS`, `REMOTE_DIR`, and
`FILE_SERVER_URL` ready for Part I.

---

## Part H — Set up the Google Sheet and Google service account

The app writes all the scraped data into a Google Sheet, using a "service
account" (a special robot account Google Cloud lets you create, which can
access specific Google Sheets you explicitly share with it — no human ever
has to log in for this to work).

### Using the sheet this project already has

This project already has a working sheet and service account set up. If
you're just re-deploying the existing app (not creating a brand-new
instance), you don't need to create anything new — just:

- **Google Sheet**: `https://docs.google.com/spreadsheets/d/1eknhrQZT8hwH58DJeeFZGOsqh7m7f7kJ1S_EZAlZ6HM/edit`
  (its ID — the long string in that URL between `/d/` and `/edit` — is your
  `SPREADSHEET_ID` value)
- **Service account email**: `python-data-scrapper@cloud-learning1.iam.gserviceaccount.com`
- Ask whoever manages this project for a copy of the service account's JSON
  key file (a small text file starting with `{"type": "service_account", ...`)
  — you'll upload its contents in Part J. Never ask for it over an insecure
  channel; a password manager or an encrypted share is best.
- Double check that email above is listed as an **Editor** on the sheet's
  **Share** settings (see step 6 below if you need to add it again).

### Setting one up from scratch (a new sheet + a new service account)

If you're setting up a completely separate/new deployment, here's the full
process:

1. **Create the Google Sheet.** Go to [sheets.new](https://sheets.new), give
   it a name. Look at the address bar — the URL looks like
   `https://docs.google.com/spreadsheets/d/LONG_ID_HERE/edit`. Copy the
   `LONG_ID_HERE` part — that's your `SPREADSHEET_ID`.
2. **Go to Google Cloud Console.** Open
   [console.cloud.google.com](https://console.cloud.google.com/) and sign in
   with a Google account.
3. **Create a project.** Click the project dropdown near the top → **New
   Project** → give it a name (e.g. `tax-rulings-scraper`) → Create.
4. **Enable the Google Sheets API.** With that project selected, go to
   **APIs & Services → Library**, search for **Google Sheets API**, open it,
   and click **Enable**.
5. **Create a service account.** Go to **APIs & Services → Credentials** →
   **+ Create Credentials → Service account**. Give it a name (e.g.
   `tax-scraper-bot`) and click through the remaining steps (the optional
   role/access screens can be skipped — this account only needs access to
   the one sheet you'll share with it directly).
6. **Create its key file.** Open the service account you just created →
   **Keys** tab → **Add Key → Create new key → JSON** → Create. A `.json`
   file downloads to your computer — this is the credentials file you'll
   upload in Part J. Keep it safe; anyone with this file can act as that
   service account.
7. **Copy the service account's email address** — it's shown on the service
   account's page, and also inside the downloaded JSON file under
   `"client_email"`. It looks like
   `something@your-project-id.iam.gserviceaccount.com`.
8. **Share the Google Sheet with it.** Open the sheet from step 1, click
   **Share** (top-right), paste the service account's email address, set its
   role to **Editor**, and click **Share**. This step is easy to forget and
   is the #1 cause of "permission denied" errors later — the JSON key file
   alone is not enough, the sheet must also explicitly grant that email
   access.

You now have everything needed for `SPREADSHEET_ID` and the credentials file
for Part J.

---

## Part I — Add all the environment variables

Environment variables are just settings the app reads on startup — things
like your Taxsutra password, the Google Sheet ID, the FTP details, etc. They
are **never** stored in the GitHub repository; they're typed directly into
Coolify.

1. On the application, go to **Configuration → Environment Variables**.
2. Click **Developer view** (top of the page) — this switches from one
   box per variable to a single big text box where you can paste many
   variables at once.
3. Copy the entire block below, paste it into that box, then go through and
   replace every `paste_..._here` placeholder with the real value you
   gathered in Parts F, G, and H (and your Taxsutra/Taxmann logins).
4. Click **Save**.

```env
# ===== Google Sheets =====
SPREADSHEET_ID=paste_your_google_sheet_id_here
SERVICE_ACCOUNT_FILE=config/credentials/service-account.json

# ===== Taxsutra.com login =====
TAXSUTRA_USERNAME=paste_taxsutra_username_here
TAXSUTRA_PASSWORD=paste_taxsutra_password_here

# ===== Taxmann.com login =====
TAXMANN_EMAIL=paste_taxmann_email_here
TAXMANN_PASSWORD=paste_taxmann_password_here

# ===== Chrome / Selenium (leave these as-is) =====
CHROME_BINARY_PATH=/usr/bin/chromium
HEADLESS_MODE=true
WEBDRIVER_TIMEOUT=8
PAGE_LOAD_WAIT=1.5
RETRY_ATTEMPTS=3

# ===== Logging (leave these as-is) =====
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log
ERROR_LOG_FILE=logs/error.log

# ===== FTP file upload (see Part G) =====
FILE_SERVER_URL=paste_your_public_files_url_here
FTP_HOST=paste_ftp_host_here
FTP_PORT=21
FTP_USER=paste_ftp_username_here
FTP_PASS=paste_ftp_password_here
LOCAL_DIR=downloads
REMOTE_DIR=paste_remote_directory_path_here

# ===== Email (see Part F) =====
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=paste_your_outlook_email_here
EMAIL_PASSWORD=paste_outlook_app_password_here
EMAIL_RECIPIENT=paste_recipient_emails_comma_separated
EMAIL_BCC=paste_bcc_emails_comma_separated

# ===== Timezone (leave as-is) =====
TIMEZONE=Asia/Kolkata
```

A couple of notes:
- `SERVICE_ACCOUNT_FILE`, `CHROME_BINARY_PATH`, the logging paths, and
  `TIMEZONE` are already correct as shown — you don't need to change those.
- After pasting, Coolify will list these as individual variables you can
  still edit one at a time later (Environment Variables page, switch back to
  **Normal view**) if you ever need to update a single value like a rotated
  password.

---

## Part J — Upload the Google service-account credentials file

The service account's JSON key file (from Part H) needs to physically exist
inside the running container at a specific path. It does **not** go into the
GitHub repo (it's a secret) — instead, Coolify has a feature called
**Persistent Storage** for exactly this.

1. Go to **Configuration → Persistent Storage**.
2. Click **+ Add → File Mount**.
3. **Destination Path**: type exactly
   `/app/config/credentials/service-account.json`
4. **Content**: open the JSON key file you downloaded (or were given) in any
   text editor, select everything, copy it, and paste it into this box
   exactly as it is — starting with `{"type": "service_account",` and ending
   with `}`. Don't reformat it or change the line breaks inside it.
5. Click **Save**.

You'll redeploy the app in Part K, which is when this file actually gets
attached to the running container.

---

## Part K — Deploy the app for the first time

1. Go to **Configuration → General** and double check the **Build Pack** is
   set to **Dockerfile** (Part E).
2. At the top-right of the application page, click **Deploy** (or
   **Actions → Redeploy** if you've deployed before and are re-running this
   after a settings change).
3. Watch the **Deployment Log** that appears. Wait for it to say
   `Rolling update completed`. A first-time build typically takes 1–3
   minutes.
4. Once deployed, the application status near the top of the page should
   show **Running**.

If a deploy ever fails, the Deployment Log will show exactly which step
failed and why — read the last red/error line first.

---

## Part L — Set up the daily Scheduled Task

The container itself just sits idle (it doesn't run the scraper on its own).
Coolify's **Scheduled Tasks** feature is what actually triggers a run, once a
day, automatically.

1. Go to **Configuration → Scheduled Tasks**.
2. Click **+ Add**.
3. Fill in:
   - **Name**: `Daily Tax Rulings Scraper`
   - **Command**: `python3 src/main.py`
   - **Frequency**: `0 8 * * *` (this means "every day at 8:00 AM" — the
     five values are minute, hour, day-of-month, month, day-of-week, and `*`
     means "any")
   - **Timeout (seconds)**: `1800` (30 minutes — the scraper can take a
     while on days with lots of rulings to check; the default of 300
     seconds is too short and would cut the run off partway through)
   - **Container name**: leave this blank
4. Click **Save**.

You can trigger a run immediately at any time (without waiting for 8 AM) by
opening the task and clicking **Execute Now** — useful the first time, to
confirm everything is wired up correctly. After it finishes, click
**Recent executions → Download Logs** to see what happened.

---

## Part M — Test that everything works

After your first **Execute Now** (or after 8 AM the next day):

1. Open the Google Sheet from Part H and confirm new rows appeared.
2. Check the inbox of whoever you put in `EMAIL_RECIPIENT` for the daily
   summary email.
3. Check the FTP directory from Part G for newly uploaded PDF files.

If any one of those three didn't happen, open **Scheduled Tasks → (the task)
→ Recent executions → Download Logs** and read through it — every step the
app takes is logged with a clear ✅ or ❌ next to it, which tells you exactly
which part didn't complete and why (e.g. a wrong password, a sheet that
isn't shared with the service account yet, and so on).

---

## 16. Quick reference

- **GitHub repo**: `git@github-shreyansmaloo:shreyansmaloo/automated-tax-rulings-scraper.git`
- **Coolify dashboard**: `http://91.108.104.17:8000` → Tax Scraper → production → automated-tax-rulings-scraper
- **Google Sheet**: `https://docs.google.com/spreadsheets/d/1eknhrQZT8hwH58DJeeFZGOsqh7m7f7kJ1S_EZAlZ6HM/edit`
- **Service account email** (must be an Editor on the sheet above): `python-data-scrapper@cloud-learning1.iam.gserviceaccount.com`
- **FTP host**: `82.112.232.12`
- **Scheduled task**: "Daily Tax Rulings Scraper" — `0 8 * * *` — `python3 src/main.py` — 1800s timeout
- **Build Pack**: Dockerfile (not Nixpacks — see Part E)
