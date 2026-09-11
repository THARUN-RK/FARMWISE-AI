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

All market, buyer, weather, and financial values in demo mode are clearly labeled estimates or simulated data.
