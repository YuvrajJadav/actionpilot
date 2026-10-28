from pathlib import Path
from flask import Flask, jsonify, render_template, request
from extractor import ExtractionError, ai_available, extract

app = Flask(__name__)
SAMPLE = Path(__file__).parent / "samples" / "meeting.txt"


@app.get("/")
def index():
    return render_template("index.html", ai=ai_available())


@app.get("/api/sample")
def sample():
    return jsonify(text=SAMPLE.read_text(encoding="utf-8"))


@app.post("/api/extract")
def extract_route():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(extract(payload.get("text"), use_ai=bool(payload.get("use_ai", True))))
    except ExtractionError as e:
        return jsonify(error=str(e)), 400


if __name__ == "__main__":
    app.run(debug=True)
