# How to deploy on Streamlit Community Cloud

1. **Get the data.** Copy your `hour.csv` into the `data/` folder of this project.
2. **Create a GitHub repo.** On github.com click **New repository**, name it e.g. `bike-sharing-app`, set it to **Public**, and create it.
3. **Upload the files.** Either use the web UI (**Add file → Upload files**) or the terminal:
   ```bash
   cd bike-sharing-app
   git init
   git add .
   git commit -m "Bike sharing Streamlit app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/bike-sharing-app.git
   git push -u origin main
   ```
   Make sure `app.py`, `requirements.txt`, `README.md` and `data/hour.csv` are all in the repo.
4. **Go to https://share.streamlit.io** and sign in with GitHub (authorize access to your repos).
5. Click **Create app → Deploy a public app from GitHub**.
6. Fill in: **Repository** = `<your-username>/bike-sharing-app`, **Branch** = `main`, **Main file path** = `app.py`.
   Optionally pick a custom URL under **App URL** (this becomes `https://<your-app>.streamlit.app`).
7. Click **Deploy**. The first build takes 1–3 minutes.
8. Copy the final URL, paste it into the **Live app** line of `README.md`, commit and push.

**Troubleshooting**
- *ModuleNotFoundError*: add the missing package to `requirements.txt` and push.
- *FileNotFoundError for data/hour.csv*: the file isn't in the repo; add it (the app also offers an upload box as a fallback).
- Changes you push to GitHub redeploy automatically.
