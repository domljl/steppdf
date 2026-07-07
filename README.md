# Step PDF

Hosted document conversion app for a small trusted group.

## Local Development

```sh
uv run uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

## Checks

```sh
uv run pytest
```

## Docker

```sh
docker build -t steppdf .
docker run --rm -p 8000:8000 steppdf
```
