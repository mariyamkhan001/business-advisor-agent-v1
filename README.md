# 🧭 Business Advisor App

A simple, beginner-friendly AI app that analyzes a business idea or business
problem you describe, and gives you:

1. **Business Analysis** — a summary of strengths and risks based only on what you wrote
2. **Recommendations** — practical next steps
3. **IP / Patent Considerations** — general education about patents, trademarks, copyrights (not legal advice)
4. **Missing Information** — what details you should add for a better analysis
5. **Action Plan** — a clear, numbered list of next steps

It's built with:
- **[Streamlit](https://streamlit.io/)** — for the web interface
- **[CrewAI](https://www.crewai.com/)** — to run a single AI "agent" (the Business Advisor)
- **[Groq](https://groq.com/)** — the AI provider, using the model `openai/gpt-oss-120b`

The AI is instructed never to make up facts. If something is missing from
your description, it will tell you instead of guessing.

---

## 📁 File Structure

```
business-advisor-app/
├── app.py                          # The main Streamlit application
├── requirements.txt                # Python packages needed to run the app
├── README.md                       # This file
├── .gitignore                      # Tells Git which files NOT to upload
└── .streamlit/
    └── secrets.toml.example        # Example of how to store your API key
```

> ⚠️ Note: `.streamlit/secrets.toml` (your REAL key file) is not included —
> you will create it yourself in Step 3 below, and it is automatically kept
> out of GitHub by `.gitignore`.

---

## ✅ Before You Start

You will need:

1. A free **Groq account** and API key → [https://console.groq.com](https://console.groq.com)
2. A free **GitHub account** → [https://github.com](https://github.com)
3. A free **Streamlit Community Cloud account** → [https://streamlit.io/cloud](https://streamlit.io/cloud) (sign in with GitHub)
4. **Python 3.11** installed on your computer (for local testing) → [https://www.python.org/downloads/](https://www.python.org/downloads/)

---

## 🪜 Step-by-Step Guide

### Step 1 — Download and organize the project folder

Save all the files provided into one folder on your computer, named exactly:

```
business-advisor-app/
```

Make sure the structure matches the **File Structure** section above,
including the `.streamlit` subfolder.

---

### Step 2 — Install the dependencies locally

Open a terminal (Command Prompt, PowerShell, or macOS/Linux Terminal),
navigate into the project folder, and run:

```bash
cd business-advisor-app

# (Recommended) Create a virtual environment first
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Now install the required packages:
pip install -r requirements.txt
```

---

### Step 3 — Get your Groq API key

1. Go to [https://console.groq.com](https://console.groq.com) and sign in (or sign up — it's free).
2. Open the **API Keys** section and click **Create API Key**.
3. Copy the key (it will look something like `gsk_xxxxxxxxxxxxxxxxxxxx`).

---

### Step 4 — Add your API key to Streamlit Secrets (for local testing)

1. Inside the `.streamlit` folder, make a **copy** of `secrets.toml.example`
   and rename the copy to exactly: `secrets.toml`
2. Open `secrets.toml` and paste your real key like this:

```toml
GROQ_API_KEY = "gsk_your_real_key_here"
```

3. Save the file. **Never share this file or upload it to GitHub** — it's
   already listed in `.gitignore` so Git will skip it automatically.

---

### Step 5 — Run the app locally

Still inside the project folder (with your virtual environment activated), run:

```bash
streamlit run app.py
```

Your browser should automatically open a tab at `http://localhost:8501`
showing the Business Advisor app. Try typing in a business idea and
clicking **Analyze My Business Idea**.

If your API key is missing or wrong, the app will show a friendly message
instead of crashing — check Step 4 again if that happens.

---

### Step 6 — Upload the project to GitHub

1. Go to [https://github.com](https://github.com) and click **New repository**.
2. Name it something like `business-advisor-app`, set it to **Public** or
   **Private** (your choice), and click **Create repository**.
3. On your computer, inside the project folder, run:

```bash
git init
git add .
git commit -m "Initial commit: Business Advisor app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/business-advisor-app.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your actual GitHub username.

> ✅ Because `secrets.toml` is in `.gitignore`, your real API key will
> **not** be uploaded to GitHub. Only `secrets.toml.example` (with no real
> key) will be visible there — which is exactly what you want.

---

### Step 7 — Deploy on Streamlit Community Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io) and sign
   in with your GitHub account.
2. Click **New app**.
3. Choose:
   - **Repository:** `YOUR-USERNAME/business-advisor-app`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Before clicking Deploy, open **Advanced settings** and set the **Python
   version** to `3.11`.
5. Click **Deploy**. Streamlit Cloud will install your `requirements.txt`
   automatically.

---

### Step 8 — Add your Groq API key to Streamlit Cloud Secrets

Your deployed app does **not** have your local `secrets.toml` file, so you
need to add the key again, directly on Streamlit Cloud:

1. Open your deployed app's page on [https://share.streamlit.io](https://share.streamlit.io).
2. Click the **⋮ (menu)** next to your app → **Settings** → **Secrets**.
3. Paste the same content as your local `secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_real_key_here"
```

4. Click **Save**. The app will automatically restart and pick up the key.

---

### Step 9 — Test the live app

Open your app's public URL (shown on the Streamlit Cloud dashboard), enter
a business idea, and click **Analyze My Business Idea**. You should see the
same five-section analysis you saw locally.

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| "Groq API key not found" | `secrets.toml` missing or key name misspelled | Make sure the key is exactly `GROQ_API_KEY` |
| "Authentication error" | Wrong or expired API key | Generate a new key on console.groq.com |
| "Rate limit reached" | Too many requests sent too quickly | Wait a minute, then try again |
| "Request timed out" | Slow network or Groq is busy | Try again in a moment |
| App works locally but not on Streamlit Cloud | Forgot to add secrets on Streamlit Cloud | Repeat Step 8 |

---

## ⚠️ Disclaimer

This app provides **general, educational business information only**. It
is **not** legal, financial, or patent/IP advice. Always consult a
qualified professional (such as a licensed attorney) before making real
business, legal, or IP decisions.
