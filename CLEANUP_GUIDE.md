# Files and Directories to Delete

## ❌ Remove these Docker-related files:
- Dockerfile
- docker-compose.yml

## ❌ Remove these old application files:
- app_full.py
- run_local.py

## ❌ Remove these build/config files (if you want minimal setup):
- Makefile
- pyproject.toml
- CODEOWNERS

## ❌ Remove these entire directories:
- docs/          (old documentation)
- monitoring/    (Prometheus/Grafana - not needed without Docker)
- scripts/       (old scripts for Docker setup)
- src/           (old source code - now in backend/)
- tests/         (if you don't need them)

## ⚠️ Optional - Remove if not using:
- frontend/      (original folder - files copied to static/)

## ✅ Keep these:
- backend/       (NEW - main application)
- static/        (NEW - frontend files)
- requirements.txt (UPDATED - minimal dependencies)
- README_NEW.md  (NEW - comprehensive guide)
- run.ps1        (NEW - Windows run script)
- run.sh         (NEW - Unix/Linux run script)
- .gitignore     (NEW)

---

## Quick Cleanup Command (PowerShell):

```powershell
# Delete files
Remove-Item Dockerfile, docker-compose.yml, app_full.py, run_local.py, Makefile, pyproject.toml, CODEOWNERS -ErrorAction SilentlyContinue

# Delete directories
Remove-Item -Recurse -Force docs, monitoring, scripts, src, tests, frontend -ErrorAction SilentlyContinue

# Rename new README
Move-Item README_NEW.md README.md -Force

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
```

## Or delete manually:
1. Delete Docker files (Dockerfile, docker-compose.yml)
2. Delete old directories (docs, monitoring, scripts, src, tests)
3. Delete old app files (app_full.py, run_local.py)
4. Keep backend/, static/, requirements.txt, README_NEW.md
5. Rename README_NEW.md to README.md
