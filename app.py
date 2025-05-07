from flask import Flask, render_template, jsonify, request, send_file
import os
import json
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

CACHE_FILE = os.path.join('static', 'data_cache.json')
RESULT_GEOJSON = os.path.join('data', 'result.geojson')

@app.route("/")
def index():
    return render_template("index.html")

def run_update(indicator, country, year):
    """
    Запускає спочатку etl.py, а потім qgis_processor.py
    """
    try:
        logging.info(f"Запуск ETL для {indicator} {country} {year}")
        etl_result = subprocess.run(
            ["python", "etl.py", "--auto", indicator, country, year],
            capture_output=True, text=True, check=True
        )
        logging.debug("ETL output:\n%s", etl_result.stdout)
        if etl_result.stderr:
            logging.warning("ETL errors:\n%s", etl_result.stderr)

        logging.info("Запуск QGIS обробки")
        qgis_result = subprocess.run(
            ["python", "qgis_processor.py"],
            capture_output=True, text=True, check=True
        )
        logging.debug("QGIS output:\n%s", qgis_result.stdout)
        if qgis_result.stderr:
            logging.warning("QGIS errors:\n%s", qgis_result.stderr)

        return True
    except subprocess.CalledProcessError as e:
        logging.error("Process error: %s", e)
        logging.error("stdout: %s", e.stdout)
        logging.error("stderr: %s", e.stderr)
        return False
    except Exception as e:
        logging.error("General error: %s", e, exc_info=True)
        return False

@app.route("/update")
def update():
    indicator = request.args.get("indicator", "population")
    country = request.args.get("country", "").strip()
    year = request.args.get("year", "2025")
    try:
        from etl import ALL_ISO_CODES
    except ImportError:
        ALL_ISO_CODES = []
    all_keys = [f"{indicator}_{iso}_{year}" for iso in ALL_ISO_CODES]
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding='utf-8') as f:
                cache_data = json.load(f)
            if all_keys and all(
                (cache_data.get("worldbank", {}).get(k) is not None or cache_data.get("api_ninjas", {}).get(k) is not None)
                for k in all_keys
            ):
                return jsonify({"status": "cached", "message": "Дані вже є в кеші для всіх країн"})
        if run_update(indicator, country, year):
            return jsonify({"status": "success", "message": f"Дані оновлено для {indicator}, {country}, {year}"})
        else:
            return jsonify({"status": "error", "message": "Помилка оновлення даних"}), 500
    except Exception as e:
        logging.exception("Error in /update")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/geojson")
def geojson():
    indicator = request.args.get("indicator", "population")
    year = request.args.get("year", "2025")
    # Формуємо шлях до відповідного result_<indicator>_<year>.geojson
    result_file = os.path.join('data', f'result_{indicator}_{year}.geojson')
    # Якщо такого немає, fallback на старий result.geojson
    if not os.path.exists(result_file):
        result_file = os.path.join('data', 'result.geojson')
    try:
        if os.path.exists(result_file):
            logging.debug(f"Sending GeoJSON from {result_file}")
            return send_file(result_file, mimetype="application/json")
        else:
            return jsonify({"error": "GeoJSON не знайдено"}), 404
    except Exception as e:
        logging.error("Error reading GeoJSON: %s", e)
        return jsonify({"error": "Помилка читання GeoJSON"}), 500


@app.route("/data")
def data():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding='utf-8') as f:
                data_output = json.load(f)
        else:
            data_output = {"worldbank": {}, "api_ninjas": {}}
        response = jsonify(data_output)
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as e:
        logging.error("Error reading cache: %s", e)
        return jsonify({"error": "Помилка читання кешу"}), 500


if __name__ == "__main__":
    app.run(debug=True)
