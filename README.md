# mini-backend

A minimal backend with two JSON endpoints, built with Flask.

## Endpoints
- `GET /hello` → `{"message": "Hello, world!"}`
- `GET /status` → `{"status": "ok", "service": "mini-backend"}`

## Run it
```bash
pip install flask
python app.py
```
Server starts at http://127.0.0.1:5000

## Test it
```bash
curl http://127.0.0.1:5000/hello
curl http://127.0.0.1:5000/status
```
Or just open those URLs in your browser.
