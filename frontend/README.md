# Motion Fighter client

Static pages served on their own origin so the browser treats them as separate from the API.

```bash
python3 server.py
```

Open http://localhost:5173.

`js/config.js` sets the API origin. Change `apiBase` when the API is deployed somewhere else. The pages send cookies with `credentials: "include"` and never hold an AI provider key.
