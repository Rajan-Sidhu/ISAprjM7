# MotionMind — Group Mr7

MotionMind is a small AI service for a four-servo desktop robot. A person describes a movement in ordinary language. The API embeds that sentence with a local copy of [google/videoprism-lvt-base-f16r288](https://huggingface.co/google/videoprism-lvt-base-f16r288) and turns the closest matches into a timed plan for the base, shoulder, elbow, and gripper.

This continues the feasibility study (four servos, Python, Flask, HTML/CSS, and a database). Login is our own email and password check. The course does not allow Google, GitHub, or other third-party sign-in. Milestone 1 plans the motion. It does not drive the microcontroller yet.

The client and the API are different origins.

| Part | Local URL |
| --- | --- |
| Client | http://localhost:5173 |
| API | http://localhost:5001 |

Demonstration accounts (passwords are stored as bcrypt hashes):

| Role | Email | Password |
| --- | --- | --- |
| User | john@john.com | 123 |
| Administrator | admin@admin.com | 111 |

## Run it

Use two terminals.

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install --no-deps "git+https://github.com/google-deepmind/videoprism.git@4f831e332b80d6e77bdd43882206f23aba2a67a7"
python download_model.py
python run.py
```

```bash
cd frontend
python3 server.py
```

Open http://localhost:5173. Sign in, ask for a motion on the user page, then sign in as the administrator and open the admin desk.

The checkpoint is `backend/models/videoprism-lvt-base-f16r288/flax_lvt_base_f16r288_repeated.npz`, the file published on the Hugging Face model page. The API loads that file from disk. `GET /api/model` reports the path. No AI provider key is used, and none is present in the browser. The second pip command is required because the VideoPrism package asks for `tensorflow-cpu`, which has no macOS build. `tensorflow` from the requirements file is used instead.

## Two public origins later

Set these on the API host:

- `CLIENT_ORIGINS` to the client origin, for example `https://myClient.xyz`
- `JWT_SECRET` to a long random value
- `COOKIE_SECURE=true` (the default)
- `PORT` to whatever the host assigns

On the client host, change `apiBase` in `frontend/js/config.js` to the API origin, for example `https://myAPI.ca`. Both sites need HTTPS so the browser will store the cross-site `HttpOnly` cookie (`SameSite=None; Secure`).

## Tests

```bash
cd backend
.venv/bin/pytest
```

## Layout

- `backend/` — Flask API, authentication, SQLite, usage log, local model
- `frontend/` — registration, user lab, administrator desk
- `docs/` — architecture, ERD, and the Milestone 1 report

Authentication, planning, administration, and the model are modules inside the API process. The client is deployed separately. User accounts, motion plans, and API usage are separate tables.
