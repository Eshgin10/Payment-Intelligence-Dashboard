# Local Windows runtime

Run commands from the project root. Runtime files and credentials are ignored by Git. The binary distribution came from the official EDB PostgreSQL download service, linked from PostgreSQL's Windows download page. PostgreSQL 17.11 runs on port 55432, with SCRAM password authentication and a loopback-only listener.

Start the existing database (only if stopped):
```powershell
.runtime\pgsql\bin\pg_ctl.exe -D .runtime\pgdata -l .runtime\postgres.log start
```
Start the backend:
```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Start the frontend in another terminal:
```powershell
cd frontend
npm.cmd run dev
```
The browser opens at http://127.0.0.1:3000. API docs are http://127.0.0.1:8000/docs. The data has already been loaded; do not rerun the seed command against this nonempty database.

Stop API/frontend with Ctrl+C in their terminals. Stop the project database:
```powershell
.runtime\pgsql\bin\pg_ctl.exe -D .runtime\pgdata stop -m fast
```

No system PATH, service, firewall or global database configuration was changed. `scripts/setup-local-db.py` is only for a new downloaded runtime and refuses to overwrite an existing database directory.
