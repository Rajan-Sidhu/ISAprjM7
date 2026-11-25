# Motion Fighter API

Flask server for accounts, motion plans, and usage statistics. See the repository README for the full run steps.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install --no-deps "git+https://github.com/google-deepmind/videoprism.git@4f831e332b80d6e77bdd43882206f23aba2a67a7"
python download_model.py
python run.py
```

The server listens on port 5001. Copy `.env.example` to `.env` before a shared deployment and change `JWT_SECRET`.

## Endpoints

| Method | Path | Who |
| --- | --- | --- |
| POST | `/api/auth/register` | public; body `{email, password}` |
| POST | `/api/auth/login` | public; body `{email, password}` |
| POST | `/api/auth/logout` | clears the cookie |
| GET | `/api/auth/me` | signed-in user |
| POST | `/api/plans` | signed-in user; body `{prompt}`; runs the local model |
| GET | `/api/plans` | signed-in user |
| GET | `/api/plans/<id>` | owner or administrator |
| DELETE | `/api/plans/<id>` | owner or administrator |
| GET | `/api/admin/users` | administrator |
| GET | `/api/admin/stats` | administrator |
| GET | `/api/model` | public; local model file location |
| GET | `/api/health` | public |
| GET | `/api/docs` | public machine-readable list |

The session is an `HttpOnly` cookie named `access_token`. Browsers must call the API with credentials included. Registration always creates a `user`. The administrator account is seeded, not chosen on the form.

## Model

`download_model.py` saves the checkpoint published at [google/videoprism-lvt-base-f16r288](https://huggingface.co/google/videoprism-lvt-base-f16r288):

`backend/models/videoprism-lvt-base-f16r288/flax_lvt_base_f16r288_repeated.npz`

The planner calls the model's text encoder. That encoder was trained together with the video encoder so a caption and a clip land in the same space. A typed motion request is a caption, so the text encoder is the part that runs for each plan. The video weights are in the same file.

## Database

SQLite file: `backend/instance/motionfighter.db`

Tables: `users`, `motion_plans`, `api_usage`. Password columns store bcrypt hashes.
