from flask import Flask, render_template, jsonify, request, send_file
import os
import json
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

CACHE_FILE = os.path.join('static', 'data_cache.json')
RESULT_GEOJSON = os.path.join('data', 'result.geojson')


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
        return False
    except Exception as e:
        logging.error("General error: %s", e)
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update")
def update():
    try:
        indicator = request.args.get("indicator", "population")
        country = request.args.get("country", "").strip()
        year = request.args.get("year", "2025")
        cache_key = f"{indicator}_{country}_{year}"

        # Спочатку перевіряємо та виправляємо кеш
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding='utf-8') as f:
                    cache_data = json.loads(f.read().strip())
            except json.JSONDecodeError:
                cache_data = {"worldbank": {}, "api_ninjas": {}}
                # Зберігаємо виправлений кеш
                with open(CACHE_FILE, "w", encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
        else:
            cache_data = {"worldbank": {}, "api_ninjas": {}}

        # Перевіряємо наявність даних у кеші
        if (cache_data.get("worldbank", {}).get(cache_key) is not None or
                cache_data.get("api_ninjas", {}).get(cache_key) is not None):
            return jsonify({"status": "cached", "message": "Дані вже є в кеші"})

        # Запускаємо оновлення даних
        if run_update(indicator, country, year):
            return jsonify({"status": "success", "message": f"Дані оновлено для {indicator}, {country}, {year}"})
        else:
            return jsonify({"status": "error", "message": "Помилка оновлення даних"}), 500

    except Exception as e:
        logging.error(f"Помилка в /update: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/geojson")
def geojson():
    try:
        if os.path.exists(RESULT_GEOJSON):
            logging.debug(f"Sending GeoJSON from {RESULT_GEOJSON}")
            return send_file(RESULT_GEOJSON, mimetype="application/json")
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
                try:
                    content = f.read().strip()  # Видаляємо зайві пробіли
                    data_output = json.loads(content)  # Використовуємо loads замість load
                except json.JSONDecodeError as e:
                    logging.error(f"Помилка декодування JSON: {e}")
                    # Створюємо новий кеш у разі помилки
                    data_output = {"worldbank": {}, "api_ninjas": {}}
                    # Зберігаємо правильний JSON
                    with open(CACHE_FILE, "w", encoding='utf-8') as f:
                        json.dump(data_output, f, ensure_ascii=False, indent=2)
        else:
            data_output = {"worldbank": {}, "api_ninjas": {}}

        response = jsonify(data_output)
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as e:
        logging.error(f"Помилка читання кешу: {e}")
        return jsonify({"error": "Помилка читання кешу"}), 500


if __name__ == "__main__":
    app.run(debug=True)
