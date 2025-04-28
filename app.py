from flask import Flask, render_template, jsonify, request
import os
import json
import subprocess
import logging

# Налаштування логування
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

CACHE_FILE = os.path.join('static', 'data_cache.json')
RESULT_GEOJSON = os.path.join('data', 'result.geojson')
BOUNDARIES_FILE = os.path.join('static', 'country_boundaries.geojson')


def run_update(indicator, country, year):
    """Запуск оновлення даних через ETL та QGIS обробку"""
    try:
        logging.info(f"Запуск ETL для {indicator} {country} {year}")
        etl_result = subprocess.run(
            ["python", "etl.py", "--auto", indicator, country, year],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug("ETL вивід:\n%s", etl_result.stdout)
        if etl_result.stderr:
            logging.warning("ETL помилки:\n%s", etl_result.stderr)

        logging.info("Запуск QGIS обробки")
        qgis_result = subprocess.run(
            ["python", "qgis_processor.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug("QGIS вивід:\n%s", qgis_result.stdout)
        if qgis_result.stderr:
            logging.warning("QGIS помилки:\n%s", qgis_result.stderr)

        return True
    except subprocess.CalledProcessError as e:
        logging.error("Помилка виконання процесу: %s", e)
        return False
    except Exception as e:
        logging.error("Загальна помилка: %s", e)
        return False


@app.route("/static/country_boundaries.geojson")
def country_boundaries():
    """Повертає GeoJSON з межами країн"""
    try:
        if os.path.exists(BOUNDARIES_FILE):
            with open(BOUNDARIES_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        logging.error("Файл меж країн не знайдено")
        return jsonify({"error": "Файл меж країн не знайдено"}), 404
    except Exception as e:
        logging.error("Помилка читання файлу меж: %s", e)
        return jsonify({"error": "Помилка читання файлу меж"}), 500


@app.route("/update")
def update():
    """Оновлення даних для вказаних параметрів"""
    indicator = request.args.get("indicator", "unemployment")
    country = request.args.get("country", "USA").strip().upper()
    year = request.args.get("year", "2025")
    cache_key = f"{indicator}_{country}_{year}"

    try:
        # Перевірка кешу
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding='utf-8') as f:
                cache_data = json.load(f)
                if (cache_data.get("worldbank", {}).get(cache_key) is not None or
                        cache_data.get("api_ninjas", {}).get(cache_key) is not None):
                    return jsonify({"status": "cached", "message": f"Дані вже є в кеші"})

        # Запуск оновлення
        if run_update(indicator, country, year):
            return jsonify({"status": "success", "message": f"Дані оновлено"})
        else:
            return jsonify({"status": "error", "message": "Помилка оновлення даних"}), 500

    except Exception as e:
        logging.error("Помилка в /update: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    """Головна сторінка"""
    return render_template("index.html")


@app.route("/data")
def data():
    """Повертає дані з кешу"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding='utf-8') as f:
                data_output = json.load(f)
        else:
            data_output = {"worldbank": {}, "api_ninjas": {}}

        response = jsonify(data_output)
        response.headers['Cache-Control'] = 'no-store'
        return response
    except Exception as e:
        logging.error("Помилка читання кешу: %s", e)
        return jsonify({"error": "Помилка читання кешу"}), 500


@app.route("/geojson")
def geojson():
    """Повертає оброблений GeoJSON"""
    try:
        if os.path.exists(RESULT_GEOJSON):
            with open(RESULT_GEOJSON, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            response = jsonify(geojson_data)
            response.headers['Cache-Control'] = 'no-store'
            return response
        else:
            return jsonify({"error": "GeoJSON не знайдено"}), 404
    except Exception as e:
        logging.error("Помилка читання GeoJSON: %s", e)
        return jsonify({"error": "Помилка читання GeoJSON"}), 500


if __name__ == "__main__":
    app.run(debug=True)