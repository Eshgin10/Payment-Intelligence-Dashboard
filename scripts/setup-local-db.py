"""Initialize the downloaded project-local PostgreSQL runtime, with loopback-only SCRAM auth."""
from pathlib import Path
import secrets
import subprocess

root=Path(__file__).resolve().parents[1]
runtime=root/'.runtime'
bin_dir=runtime/'pgsql/bin'
data_dir=runtime/'pgdata'
if data_dir.exists():
    raise SystemExit('Database directory already exists; no changes made.')
password=secrets.token_urlsafe(32)
pwfile=runtime/'init-password'
pwfile.write_text(password)
try:
    subprocess.run([str(bin_dir/'initdb.exe'),'-D',str(data_dir),'-U','payment','-A','scram-sha-256','--pwfile',str(pwfile),'-E','UTF8','--locale=C'],check=True)
finally:
    pwfile.unlink(missing_ok=True)
with (data_dir/'postgresql.conf').open('a') as f:
    f.write("\nlisten_addresses = '127.0.0.1'\nport = 55432\n")
env_path=root/'.env'
if env_path.exists(): raise SystemExit('Existing .env preserved. Configure DATABASE_URL manually for the new cluster.')
env_path.write_text(f'DATABASE_URL=postgresql://payment:{password}@127.0.0.1:55432/payment_intelligence\nAPI_ORIGIN=http://127.0.0.1:8000\n')
print('Initialized loopback-only PostgreSQL. Credentials saved to ignored .env.')
