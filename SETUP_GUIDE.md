# Timber AI Assistant V26 — Setup Guide
### From zero to live in the cloud, step by step

---

## What you will set up
1. GitHub — stores your app code
2. Google Cloud + Google Sheets — stores your quote history
3. Streamlit Community Cloud — runs your app online (free)

**Total time: about 30–40 minutes, one time only.**
After this, the app runs 24/7. You just open the URL on any device.

---

## PART 1 — Upload your code to GitHub

### Step 1 — Create a GitHub account (skip if you have one)
1. Open your browser and go to **https://github.com**
2. Click the green **"Sign up"** button
3. Enter your email, create a password, choose a username
4. Verify your email when GitHub sends you a confirmation

### Step 2 — Create a new repository
1. After logging in, click the **"+"** icon at the top right of the screen
2. Click **"New repository"**
3. In the **"Repository name"** box, type: `timber-ai-v26`
4. Make sure **"Public"** is selected (required for free Streamlit hosting)
5. Tick the box **"Add a README file"**
6. Click the green **"Create repository"** button
7. You will see a page with your new empty repository

### Step 3 — Upload your files
You have 4 files to upload:
- `app.py`
- `requirements.txt`
- `.gitignore`
- `secrets.toml.template`

Do this:
1. On your repository page, click **"Add file"** → **"Upload files"**
2. Drag all 4 files into the upload area (or click "choose your files")
3. Scroll down and click the green **"Commit changes"** button
4. Wait a few seconds — you will see all 4 files listed in your repository

---

## PART 2 — Set up Google Sheets to store quotes

### Step 4 — Create the Google Sheet
1. Go to **https://sheets.google.com** using your **new Gmail account**
2. Click the **"+"** button to create a blank spreadsheet
3. Click on **"Untitled spreadsheet"** at the top and rename it to exactly:
   ```
   Timber Quotes V26
   ```
   *(spelling and capital letters must match exactly)*
4. In **Row 1**, type these headers in each cell:
   - A1: `Date`
   - B1: `Time`
   - C1: `Customer Name`
   - D1: `Mobile`
   - E1: `Items`
   - F1: `Total (SGD)`
   - G1: `Quote Text`
5. Make row 1 bold (select row 1, press Ctrl+B)
6. Leave the sheet open — you will need its URL later

### Step 5 — Create a Google Cloud project
1. Go to **https://console.cloud.google.com**
2. Sign in with your **new Gmail account**
3. At the very top, click **"Select a project"** → then click **"New Project"**
4. In the **"Project name"** box, type: `TimberApp`
5. Click **"Create"** and wait about 10 seconds for it to finish
6. Make sure **"TimberApp"** is selected in the top dropdown before continuing

### Step 6 — Enable Google Sheets API
1. In the left menu, click **"APIs & Services"** → **"Library"**
2. In the search box, type `Google Sheets API`
3. Click on **"Google Sheets API"** in the results
4. Click the blue **"Enable"** button
5. Wait for it to enable (about 5 seconds)
6. Go back and also search for `Google Drive API` — enable that one too

### Step 7 — Create a Service Account
A service account is like a robot login that lets your app write to Google Sheets automatically.

1. In the left menu, click **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** at the top → select **"Service account"**
3. In **"Service account name"** type: `timber-app`
4. Click **"Create and continue"**
5. In the **"Role"** dropdown, select **"Editor"**
6. Click **"Continue"** then **"Done"**
7. You will see your new service account listed — click on it
8. Click the **"Keys"** tab at the top
9. Click **"Add Key"** → **"Create new key"**
10. Select **"JSON"** and click **"Create"**
11. A JSON file will automatically download to your computer — **keep this file safe, do not share it**

### Step 8 — Share your Google Sheet with the service account
1. Open the JSON file you just downloaded in Notepad (right-click → Open with → Notepad)
2. Find the line that says `"client_email"` — copy the email address value (looks like `timber-app@timberapp.iam.gserviceaccount.com`)
3. Go back to your **"Timber Quotes V26"** Google Sheet
4. Click the **"Share"** button (top right, green)
5. Paste the service account email into the share box
6. Set permission to **"Editor"**
7. Untick **"Notify people"**
8. Click **"Share"**

---

## PART 3 — Deploy on Streamlit Community Cloud

### Step 9 — Create Streamlit account
1. Go to **https://share.streamlit.io**
2. Click **"Sign up"**
3. Sign up using your **GitHub account** (click "Continue with GitHub")
4. Authorise Streamlit to access your GitHub

### Step 10 — Deploy your app
1. Click **"New app"** button
2. In **"Repository"**, select `timber-ai-v26`
3. In **"Branch"**, leave as `main`
4. In **"Main file path"**, type `app.py`
5. Click **"Advanced settings"** — you will add secrets here in the next step
6. Do NOT click Deploy yet

### Step 11 — Add your secrets to Streamlit
This is where you connect your Google Sheets credentials. Do NOT put these in GitHub.

1. In the Advanced settings, find the **"Secrets"** text box
2. Open your downloaded JSON key file in Notepad
3. Open the file `secrets.toml.template` in Notepad
4. Fill in the secrets template by copying values from the JSON file:

| In secrets.toml.template | Copy from JSON file |
|--------------------------|---------------------|
| `project_id` | `"project_id"` value |
| `private_key_id` | `"private_key_id"` value |
| `private_key` | `"private_key"` value (include the full key with \n characters) |
| `client_email` | `"client_email"` value |
| `client_id` | `"client_id"` value |
| `client_x509_cert_url` | `"client_x509_cert_url"` value |

5. Paste the completed secrets into the Streamlit secrets box
6. Make sure `sheet_name = "Timber Quotes V26"` is at the top
7. Click **"Save"**

### Step 12 — Deploy!
1. Click the **"Deploy!"** button
2. Streamlit will take about 2–3 minutes to build your app
3. You will see a progress log — wait for it to finish
4. When done, your app opens automatically in the browser

---

## PART 4 — Access your app anywhere

### Step 13 — Get your app URL
1. Your app URL looks like: `https://your-app-name.streamlit.app`
2. Copy this URL
3. **Bookmark it on your phone browser** — this is how you access it when outstation
4. You can also add it to your phone home screen:
   - On iPhone: open in Safari → Share → "Add to Home Screen"
   - On Android: open in Chrome → menu (3 dots) → "Add to Home screen"

---

## Troubleshooting

**App shows "Google Sheets not connected" warning**
→ Check that your secrets are entered correctly in Streamlit Cloud settings
→ Make sure the sheet name matches exactly: `Timber Quotes V26`
→ Make sure the service account email is shared on the Google Sheet as Editor

**"Module not found" error**
→ Check that `requirements.txt` was uploaded to GitHub correctly

**Quotes not saving**
→ Check the service account has Editor access to the sheet
→ Make sure Google Sheets API and Google Drive API are both enabled

**App is slow to load first time**
→ Normal — Streamlit Cloud "sleeps" free apps after 7 days of no use
→ First load after sleep takes about 30 seconds, then it's fast

---

## After setup — daily use

1. Open your app URL (bookmark or phone home screen)
2. Enter customer name + mobile
3. Fill in the timber/plywood table
4. Click **Generate Quote**
5. Edit the customer reply text as needed
6. Click **Save to History** — saved to Google Sheets instantly
7. Copy and send to customer via WhatsApp or email

**To check past quotes when outstation:**
- Open app URL on your phone
- Go to **Quote History** tab
- Type customer name or mobile in the search box
- Tap to expand and read the full quote

---

## Files in your GitHub repository

| File | Purpose |
|------|---------|
| `app.py` | Main app code |
| `requirements.txt` | Python packages needed |
| `.gitignore` | Prevents secrets from uploading |
| `secrets.toml.template` | Secrets format reference (safe to upload) |

**Never upload your actual `secrets.toml` or the JSON key file to GitHub.**

---

*Timber AI Assistant V26 — Built for TimMac @ Kranji*
