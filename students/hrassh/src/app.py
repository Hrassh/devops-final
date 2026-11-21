import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from converter import UNITS, ConversionError, convert

APP_ENV = os.environ.get("APP_ENV", "development")
APP_VERSION = os.environ.get("APP_VERSION", "local")

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", units=UNITS, version=APP_VERSION, env=APP_ENV)


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        version=APP_VERSION,
        env=APP_ENV,
        time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


@app.get("/api/units")
def units():
    return jsonify({category: list(items) for category, items in UNITS.items()})


@app.get("/api/convert")
def api_convert():
    category = request.args.get("category", "")
    from_unit = request.args.get("from", "")
    to_unit = request.args.get("to", "")
    try:
        value = float(request.args.get("value", ""))
    except ValueError:
        return jsonify(error="value must be a number"), 400
    try:
        result = convert(category, value, from_unit, to_unit)
    except ConversionError as error:
        return jsonify(error=str(error)), 400
    return jsonify(category=category, value=value, from_unit=from_unit, to_unit=to_unit, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
