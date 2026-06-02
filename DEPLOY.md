# Deploying Skin Triage live

This app is set up to deploy on **[Render](https://render.com)** with a free
Postgres database, using the included `render.yaml` blueprint. ~5 minutes.

## Steps

1. **Create a Render account** at https://render.com (sign in with GitHub —
   it's free, no credit card needed for the free tier).

2. In the Render dashboard, click **New +** → **Blueprint**.

3. **Connect your GitHub** and pick the `skin-triage-api` repository.
   Render reads `render.yaml` and shows two resources to create:
   - `skin-triage-api` (the web service)
   - `skin-triage-db` (a free Postgres database)

4. Click **Apply**. Render will:
   - create the database,
   - install dependencies (`pip install -r requirements.txt`),
   - inject the database URL and a generated `SECRET_KEY`,
   - start the server and run the health check at `/health`.

5. When the build finishes (a few minutes), open the service URL Render gives
   you, e.g. `https://skin-triage-api.onrender.com` — your app is live. 🎉

## Notes

- **Free tier sleeps after ~15 min idle.** The first visit after a nap takes
  ~30-60s to wake — same as the Hugging Face model behind it.
- **The model**: predictions are served by the Hugging Face Space
  (`sweety783/skin-disease-classifier`), which also sleeps and wakes. The first
  prediction after idle may take up to a minute; the app retries automatically.
- **Tables** are created automatically on first startup. No manual migration
  step is needed for the initial deploy.
- To change the model endpoint, set the `HF_SPACE_URL` env var in Render.

## Alternative: Railway

Railway also works: create a project from the repo, add a PostgreSQL plugin,
and set `DATABASE_URL` to the plugin's connection string. The same start
command applies: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
