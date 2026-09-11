# FarmWise AI

India-realistic crop-to-market decision intelligence for farmers.

FarmWise connects farm conditions to crop recommendations, sowing windows, market net realization, buyer matching, enquiries, and impact estimates.

## Live frontend

After GitHub Pages finishes its first deployment, the frontend is available at:

`https://tharun-rk.github.io/FARMWISE-AI/`

The repository URL is the source-code page, not the running application.

## Local development

```powershell
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173/`

Backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe scripts\seed_database.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

## Demo account

```text
Phone: +919999999999
Password: DemoPass123!
```

The frontend Demo Mode works without the backend. Real login, personalized farm data, and recommendations require the FastAPI backend to be running or deployed and configured through `VITE_API_URL`.

## Deployment

The frontend deploys through `.github/workflows/deploy-pages.yml`. The backend requires a separate Python hosting target such as Azure Container Apps, Render, Railway, or a VPS with PostgreSQL.

If the Pages settings are using branch deployment instead of Actions, set **Settings -> Pages -> Deploy from a branch -> `main` -> `/docs`**. The compiled frontend artifact is committed in `docs/`; do not select `/ (root)`, because the root `index.html` is the Vite development entry and will request `/src/main.tsx`.

### Deploy the backend on Render

1. Create a new Render Blueprint from this repository.
2. Select `backend/render.yaml`.
3. Wait for the web service and PostgreSQL database to become healthy.
4. Copy the API URL, for example `https://farmwise-ai-api.onrender.com`.
5. Set the GitHub repository variable `VITE_API_URL` to `https://farmwise-ai-api.onrender.com/api/v1`.
6. Run the Pages workflow again.

Until this is configured, signup and login work only when the local FastAPI server is running. Demo Mode does not need the backend.

All market, buyer, weather, and financial values in demo mode are clearly labeled estimates or simulated data.
