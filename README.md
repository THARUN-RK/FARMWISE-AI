# FarmWise AI

India-realistic crop-to-market decision intelligence for farmers.

FarmWise connects farm conditions to crop recommendations, sowing windows, market net realization, buyer matching, enquiries, and impact estimates.

Farmers can upload crop photos or short videos (up to 10 MB) with harvest
details. Farmers and buyers have separate workspaces and can message each other
in private conversations. Phone, email, and precise location are hidden unless
the account owner explicitly opts in to sharing them in that conversation.
Farmers can also compare low, expected, and high farm budget/profit scenarios;
these are explainable planning estimates, not a trained AI model or a guarantee.

The Online Marketplaces workspace links to [Farmizen Farmers' Markets](https://www.farmizen.com/farmers-markets)
and [CommodityOnline](https://www.commodityonline.com/). The language selector
includes English and all 22 constitutionally scheduled Indian languages. Built-in
translations are available for English, Hindi, Kannada, Telugu, and Tamil.
Selected interface strings for other languages can be fetched from
`/api/v1/translate/interface-strings/{language}` when
`GOOGLE_TRANSLATE_API_KEY` is configured on the backend. This does not yet
translate every screen or all 22 languages; some language codes are mapped to
nearby languages or remain English. Only fixed interface strings are sent for
translation—user data (crop notes, profiles, private messages) is not.

## Live frontend

After GitHub Pages finishes its first deployment, the frontend is available at:

`https://tharun-rk.github.io/FARMWISE-AI/`

The repository URL is the source-code page, not the running application.

## Local development

```powershell
npm install
npm run dev
```

Open the frontend at `http://localhost:5173/FARMWISE-AI/`. Keep the Vite
terminal running, and start the backend in a second terminal:

Backend:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe scripts\seed_database.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
Pop-Location
```

Swagger: `http://localhost:8000/docs`

## Demo account

```text
Phone: +919999999999
Password: DemoPass123!
```

The frontend Demo Mode works without the backend. Real login, personalized farm data, and recommendations require the FastAPI backend to be running or deployed and configured through `VITE_API_URL`.

The supplied Google OAuth Web client ID is configured as the frontend and
backend default. You can override it with `VITE_GOOGLE_CLIENT_ID` for the
frontend build and `GOOGLE_CLIENT_ID` on the backend; both values must match.
Docker Compose forwards the backend setting into the API container.

To enable Google sign-in, create a Google OAuth **Web application** client and
add these exact origins as authorized JavaScript origins (origins have no path):

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `https://tharun-rk.github.io`

Set `VITE_GOOGLE_CLIENT_ID` for the frontend build and the same value as
`GOOGLE_CLIENT_ID` on the backend. For GitHub Pages, also set `VITE_API_URL`
to your deployed backend URL ending in `/api/v1`, then rebuild/redeploy the
frontend. Google Identity Services uses its JavaScript popup flow here, so do
not add the GitHub Pages URL as an OAuth redirect URI. A new Google account
must also provide a phone number to create its farmer profile.

Profile location is opt-in: farmers can press **Use my current location** and
approve the browser permission. The app saves that one-time location to their
account; it does not continuously track location in the background.

## Deployment

The frontend deploys through `.github/workflows/deploy-pages.yml`; set GitHub Pages to **GitHub Actions**. Production bundles are built by the workflow and are not committed. The backend requires a separate Python hosting target such as Azure Container Apps, Render, Railway, or a VPS with PostgreSQL.

### Deploy the backend on Render

1. Create a new Render Blueprint from this repository.
2. Select `backend/render.yaml`.
3. Wait for the web service and PostgreSQL database to become healthy.
4. Copy the API URL shown on your Render service. The currently deployed API is `https://farmwise-ai-1-8hi6.onrender.com` (the retired `farmwise-ai-api.onrender.com` address returns 404).
5. Set the GitHub repository variable `VITE_API_URL` to `<your-render-api-url>/api/v1`, for example `https://farmwise-ai-1-8hi6.onrender.com/api/v1`.
6. Set the GitHub repository variable `VITE_GOOGLE_CLIENT_ID` to your Google OAuth Web client ID, and set the same ID as `GOOGLE_CLIENT_ID` on Render.
7. To translate the interface, enable the Google Cloud Translation API (v2) with billing and add its API key as the Render secret `GOOGLE_TRANSLATE_API_KEY`. The key must be kept on the backend; do not add it to GitHub Pages or commit it.
8. Add `https://tharun-rk.github.io` to the OAuth client's authorized JavaScript origins, then run the Pages workflow again.

Until this is configured, signup and login work only when the local FastAPI server is running. Demo Mode does not need the backend.

All market, buyer, weather, and financial values in demo mode are clearly labeled estimates or simulated data.
