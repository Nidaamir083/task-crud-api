from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/hello")
def hello():
    return jsonify({"message": "Hello, world!"})

@app.route("/status")
def status():
    return jsonify({"status": "ok", "service": "mini-backend"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
