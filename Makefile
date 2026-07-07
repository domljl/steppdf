.PHONY: start

start:
	pnpm -C frontend build
	uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
