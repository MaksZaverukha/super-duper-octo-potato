import os
import json
import requests
import logging
import xml.etree.ElementTree as ET
import sys
import glob
import urllib.parse

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Тепер результати записуються у data/input.geojson
INPUT_GEOJSON = os.path.join("data", "input.geojson")

API_KEY = "5V7O0c43JxoQZRUQtqla3Q==xfXFKSRNZW0CR5jj"
HEADERS = {"X-Api-Key": API_KEY}

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country"
PER_PAGE = 1000

INDICATORS = {
    "unemployment": {
        "name": "Рівень безробіття",
        "api_ninjas_url": "https://api.api-ninjas.com/v1/unemployment",
        "worldbank_indicator": "SL.UEM.TOTL.ZS",
        "api_field": "unemployment_rate"
    },
    "population": {
        "name": "Населення",
        "api_ninjas_url": "https://api.api-ninjas.com/v1/population",
        "worldbank_indicator": "SP.POP.TOTL",
        "api_field": "population"
    }
}


def fetch_api_ninjas_data(url, year_filter, api_field, indicator_key):
    logging.debug(f"Request to API Ninjas: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        req_year = int(year_filter)
        features = []
        if (indicator_key == "population" and isinstance(data, dict) and (
                "historical_population" in data or "population_forecast" in data)):
            arr = []
            if "historical_population" in data and any(
                    int(item.get("year", 0)) == req_year for item in data["historical_population"]):
                arr = data["historical_population"]
            elif "population_forecast" in data and any(
                    int(item.get("year", 0)) == req_year for item in data["population_forecast"]):
                arr = data["population_forecast"]
            else:
                logging.info(f"No population records found for year {req_year} in API Ninjas response.")
            for entry in arr:
                try:
                    if int(entry.get("year", 0)) == req_year:
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "source": "api_ninjas",
                                "country": data.get("country_name"),
                                "year": entry.get("year"),
                                api_field: entry.get(api_field)
                            },
                            "geometry": None
                        })
                except (ValueError, TypeError):
                    continue
        elif isinstance(data, list):
            for entry in data:
                try:
                    if int(entry.get("year", 0)) == req_year:
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "source": "api_ninjas",
                                "country": entry.get("country"),
                                "year": entry.get("year"),
                                api_field: entry.get(api_field)
                            },
                            "geometry": {"type": "Point",
                                         "coordinates": [entry.get("longitude"), entry.get("latitude")]}
                            if ("longitude" in entry and "latitude" in entry) else None
                        })
                except (ValueError, TypeError):
                    continue
        else:
            logging.warning("Unexpected data structure returned from API Ninjas.")
        logging.debug(f"Fetched {len(features)} features from API Ninjas for year {year_filter}.")
        return features
    except Exception as e:
        logging.error(f"Error fetching API Ninjas data: {e}")
        return []


def download_and_save_worldbank_xml(indicator, year_filter):
    output_dir = os.path.join("data", "worldbank")
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"worldbank_{indicator}_{year_filter}.xml"
    file_path = os.path.join(output_dir, file_name)
    if os.path.exists(file_path):
        logging.info(f"Using cached World Bank XML: {file_path}")
        return file_path
    url = f"{WORLD_BANK_BASE_URL}/all/indicator/{indicator}?format=xml&date={year_filter}:{year_filter}&per_page={PER_PAGE}"
    logging.debug(f"World Bank API request: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        logging.info(f"Downloaded World Bank XML: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error downloading World Bank XML: {e}")
        return None


def fetch_worldbank_data_all(indicator, year_filter, worldbank_field):
    file_path = download_and_save_worldbank_xml(indicator, year_filter)
    if not file_path:
        return {"type": "FeatureCollection", "features": []}
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        logging.error(f"Error parsing World Bank XML: {e}")
        return {"type": "FeatureCollection", "features": []}
    features = []
    for rec in list(root):
        rec_country = None
        rec_year = None
        rec_value = None
        for child in rec:
            tag = child.tag.split("}")[-1]
            if tag == "countryiso3code" and child.text:
                rec_country = child.text.strip().upper()
            elif tag == "date":
                try:
                    rec_year = int(child.text)
                except Exception:
                    rec_year = None
            elif tag == "value":
                try:
                    rec_value = float(child.text) if child.text else None
                except Exception:
                    rec_value = None
        if rec_year != int(year_filter):
            continue
        if rec_country is None or rec_value is None:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "source": "worldbank_xml",
                "country": rec_country,
                "year": rec_year,
                worldbank_field: rec_value
            },
            "geometry": None
        })
    logging.debug(f"World Bank features generated: {len(features)}")
    return {"type": "FeatureCollection", "features": features}


def generate_geojson(indicator_key, country_input=None, year_input=None):
    if indicator_key not in INDICATORS:
        logging.error("Invalid indicator!")
        return
    config = INDICATORS[indicator_key]
    logging.info(f"Loading data for {config['name']}")
    if year_input is None:
        year_input = "2025"

    if int(year_input) <= 2023:
        fc = fetch_worldbank_data_all(config["worldbank_indicator"], year_input, config["api_field"])
    else:
        if country_input and country_input.strip().upper() != "ALL":
            encoded_country = urllib.parse.quote(country_input.strip())
            ninjas_url = f"{config['api_ninjas_url']}?country={encoded_country}"
            features = fetch_api_ninjas_data(ninjas_url, year_input, config["api_field"], indicator_key)
            fc = {"type": "FeatureCollection", "features": features}
        else:
            logging.warning("For future years, a valid country must be provided (not 'ALL').")
            fc = {"type": "FeatureCollection", "features": []}

    try:
        os.makedirs("data", exist_ok=True)
        with open(INPUT_GEOJSON, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
        logging.info(f"Input GeoJSON written to {INPUT_GEOJSON} with {len(fc.get('features', []))} features.")
    except Exception as e:
        logging.error(f"Error saving input GeoJSON: {e}")

    cache_data = {"worldbank": {}, "api_ninjas": {}}
    for feature in fc.get("features", []):
        props = feature.get("properties", {})
        country_val = props.get("country")
        field_val = props.get(config["api_field"])
        if country_val:
            key = f"{indicator_key}_{country_val}_{year_input}"
            if props.get("source") == "worldbank_xml":
                cache_data["worldbank"][key] = field_val
            else:
                cache_data["api_ninjas"][key] = field_val
    os.makedirs("static", exist_ok=True)
    try:
        with open(os.path.join("static", "data_cache.json"), "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logging.info("Cache updated: static/data_cache.json")
    except Exception as e:
        logging.error(f"Error saving cache: {e}")


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--auto":
        generate_geojson(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        logging.info("Available indicators:")
        for key, value in INDICATORS.items():
            logging.info(f"{key}: {value['name']}")
        selected_indicator = input("Indicator (population or unemployment): ").strip()
        selected_country = input("Country (for years > 2023, e.g., Kazakhstan): ").strip()
        year_selected = input("Year: ").strip()
        generate_geojson(selected_indicator, selected_country, year_selected)
