import os
import json
import requests
import logging
import xml.etree.ElementTree as ET
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INPUT_GEOJSON = "data/input.geojson"

API_KEY = "/mkGQOXLPthytx85xlMdyw==0Jmv7Gs6bwa2Bj0L"
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

def fetch_api_ninjas_data(url, year_filter, api_field):
    try:
        logging.debug(f"Request to API Ninjas: {url}")
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        try:
            year_filter_int = int(year_filter)
        except ValueError:
            logging.error("Year format error; year must be a number.")
            return []
        filtered = [entry for entry in data if entry.get("year") == year_filter_int]
        logging.debug(f"Filtered data for {year_filter_int}: {filtered}")
        features = []
        for entry in filtered:
            coords = [entry["longitude"], entry["latitude"]] if "longitude" in entry and "latitude" in entry else None
            feature = {
                "type": "Feature",
                "properties": {
                    "source": "api_ninjas",
                    "country": entry.get("country"),
                    "year": entry.get("year"),
                    api_field: entry.get(api_field)
                },
                "geometry": {"type": "Point", "coordinates": coords} if coords else None
            }
            features.append(feature)
        return features
    except Exception as e:
        logging.error(f"Error fetching API Ninjas data: {e}")
        return []

def download_and_save_worldbank_xml(indicator, year_filter):
    output_dir = os.path.join("data", "worldbank")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"worldbank_{indicator}_{year_filter}.xml")
    if os.path.exists(output_file):
        logging.info(f"XML file already exists: {output_file}")
        return output_file
    url = f"{WORLD_BANK_BASE_URL}/all/indicator/{indicator}?format=xml&date={year_filter}:{year_filter}&per_page={PER_PAGE}"
    logging.debug(f"World Bank API request: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        xml_data = response.content
        with open(output_file, "wb") as f:
            f.write(xml_data)
        logging.info(f"XML file saved: {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"Error downloading World Bank XML: {e}")
        return None

def fetch_worldbank_data_all(indicator, country_input, year_filter, worldbank_field):
    user_country_code = country_input.strip().upper()
    file_path = download_and_save_worldbank_xml(indicator, year_filter)
    if not file_path:
        return []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        logging.error(f"Error parsing XML file: {e}")
        return []
    features = []
    records = list(root)
    logging.debug(f"Found {len(records)} records in XML.")
    for rec in records:
        rec_country_code = None
        rec_year = None
        rec_value = None
        for child in rec:
            tag = child.tag.split('}')[-1]
            if tag == 'countryiso3code':
                if child.text:
                    rec_country_code = child.text.strip().upper()
            elif tag == 'date':
                try:
                    rec_year = int(child.text)
                except Exception:
                    rec_year = None
            elif tag == 'value':
                try:
                    rec_value = float(child.text) if child.text else None
                except Exception:
                    rec_value = None
        if rec_country_code is None or rec_year is None or rec_value is None:
            continue
        if rec_country_code != user_country_code or rec_year != int(year_filter):
            continue
        feature = {
            "type": "Feature",
            "properties": {
                "source": "worldbank_xml",
                "country": rec_country_code,
                "year": rec_year,
                worldbank_field: rec_value
            },
            "geometry": None
        }
        features.append(feature)
    logging.debug(f"Generated {len(features)} features from World Bank XML.")
    return features

def generate_geojson(indicator_key, country_input=None, year_input=None):
    if indicator_key not in INDICATORS:
        logging.error("Invalid indicator!")
        return
    indicator_obj = INDICATORS[indicator_key]
    logging.info(f"Loading data for indicator: {indicator_obj['name']}")
    if country_input is None:
        country_input = "USA"
    if year_input is None:
        year_input = "2025"
    ninjas_url = f"{indicator_obj['api_ninjas_url']}?country={country_input}"
    logging.debug(f"API Ninjas URL: {ninjas_url}")
    ninjas_features = fetch_api_ninjas_data(ninjas_url, year_input, indicator_obj["api_field"])
    worldbank_features = fetch_worldbank_data_all(indicator_obj["worldbank_indicator"], country_input, year_input, indicator_obj["api_field"])
    features = ninjas_features + worldbank_features
    if not features:
        logging.warning(f"No data for {country_input} in {year_input} from both sources!")
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    os.makedirs("data", exist_ok=True)
    try:
        with open(INPUT_GEOJSON, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        logging.info(f"GeoJSON saved: {INPUT_GEOJSON}")
    except Exception as e:
        logging.error(f"Error saving GeoJSON: {e}")
    worldbank_cache = {}
    for feature in worldbank_features:
        props = feature.get("properties", {})
        iso = props.get("country")
        val = props.get(indicator_obj["api_field"])
        if iso:
            key = indicator_key + "_" + iso + "_" + year_input
            worldbank_cache[key] = val
    ninjas_cache = {}
    for feature in ninjas_features:
        props = feature.get("properties", {})
        iso = props.get("country")
        val = props.get(indicator_obj["api_field"])
        if iso:
            key = indicator_key + "_" + iso + "_" + year_input
            ninjas_cache[key] = val

    cache_data = {"worldbank": worldbank_cache, "api_ninjas": ninjas_cache}
    os.makedirs("static", exist_ok=True)
    try:
        with open(os.path.join("static", "data_cache.json"), "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logging.info("Cache updated: static/data_cache.json")
    except Exception as e:
        logging.error(f"Error saving cache: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--auto":
        indicator = sys.argv[2]
        country = sys.argv[3]
        year = sys.argv[4]
        generate_geojson(indicator, country, year)
    elif len(sys.argv) > 1 and sys.argv[1] == "--auto":
        generate_geojson("unemployment", "USA", "2025")
    else:
        logging.info("Available indicators:")
        for key, value in INDICATORS.items():
            logging.info(f"{key}: {value['name']}")
        selected_indicator = input("Choose indicator (e.g., unemployment or population): ").strip()
        generate_geojson(selected_indicator)
