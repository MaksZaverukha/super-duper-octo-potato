#!/usr/bin/env python
import os
import json
import requests
import logging
import xml.etree.ElementTree as ET
import sys
import urllib.parse
import shutil  # Для копіювання файлів

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Файл для запису вхідного GeoJSON (для сумісності з іншими модулями, наприклад, qgis_processor.py)
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

# Список ISO‑кодів (згідно з вашим script.js/countryMapping)
ALL_ISO_CODES = [
    "AFG", "ALB", "DZA", "AND", "AGO", "ARG", "ARM", "AUS", "AUT", "AZE",
    "BHS", "BHR", "BGD", "BRB", "BLR", "BEL", "BLZ", "BEN", "BTN", "BOL",
    "BIH", "BWA", "BRA", "BRN", "BGR", "BFA", "BDI", "KHM", "CMR", "CAN",
    "CPV", "CAF", "TCD", "CHL", "CHN", "COL", "COM", "COG", "CRI", "CIV",
    "HRV", "CUB", "CYP", "CZE", "COD", "DNK", "DJI", "DMA", "DOM", "ECU",
    "EGY", "SLV", "GNQ", "ERI", "EST", "SWZ", "ETH", "FJI", "FIN", "FRA",
    "GAB", "GMB", "GEO", "DEU", "GHA", "GRC", "GRD", "GTM", "GIN", "GNB",
    "GUY", "HTI", "HND", "HUN", "ISL", "IND", "IDN", "IRN", "IRQ", "IRL",
    "ISR", "ITA", "JAM", "JPN", "JOR", "KAZ", "KEN", "KIR", "PRK", "KOR",
    "KWT", "KGZ", "LAO", "LVA", "LBN", "LSO", "LBR", "LBY", "LIE", "LTU",
    "LUX", "MDG", "MWI", "MYS", "MDV", "MLI", "MLT", "MHL", "MRT", "MUS",
    "MEX", "FSM", "MDA", "MCO", "MNG", "MNE", "MAR", "MOZ", "MMR", "NAM",
    "NRU", "NPL", "NLD", "NZL", "NIC", "NER", "NGA", "MKD", "NOR", "OMN",
    "PAK", "PLW", "PSE", "PAN", "PNG", "PRY", "PER", "PHL", "POL", "PRT",
    "QAT", "ROU", "RUS", "RWA", "KNA", "LCA", "VCT", "WSM", "SMR", "STP",
    "SAU", "SEN", "SRB", "SYC", "SLE", "SGP", "SVK", "SVN", "SLB", "SOM",
    "ZAF", "SSD", "ESP", "LKA", "SDN", "SUR", "SWE", "CHE", "SYR", "TWN",
    "TJK", "TZA", "THA", "TLS", "TGO", "TON", "TTO", "TUN", "TUR", "TKM",
    "TUV", "UGA", "UKR", "ARE", "GBR", "USA", "URY", "UZB", "VUT", "VEN",
    "VNM", "YEM", "ZMB", "ZWE", "GRL", "ATF"
]

# --- Country name to ISO mapping (згенеровано на основі countryMapping з script.js) ---
COUNTRY_NAME_TO_ISO = {
    "Afghanistan": "AFG",
    "Albania": "ALB",
    "Algeria": "DZA",
    "Andorra": "AND",
    "Angola": "AGO",
    "Argentina": "ARG",
    "Armenia": "ARM",
    "Australia": "AUS",
    "Austria": "AUT",
    "Azerbaijan": "AZE",
    "Bahamas": "BHS",
    "Bahrain": "BHR",
    "Bangladesh": "BGD",
    "Barbados": "BRB",
    "Belarus": "BLR",
    "Belgium": "BEL",
    "Belize": "BLZ",
    "Benin": "BEN",
    "Bhutan": "BTN",
    "Bolivia": "BOL",
    "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA",
    "Brazil": "BRA",
    "Brunei Darussalam": "BRN",
    "Bulgaria": "BGR",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cambodia": "KHM",
    "Cameroon": "CMR",
    "Canada": "CAN",
    "Cape Verde": "CPV",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "Chile": "CHL",
    "China": "CHN",
    "Colombia": "COL",
    "Comoros": "COM",
    "Congo": "COG",
    "Costa Rica": "CRI",
    "Ivory Coast": "CIV",
    "Croatia": "HRV",
    "Cuba": "CUB",
    "Cyprus": "CYP",
    "Czechia": "CZE",
    "Democratic Republic of the Congo": "COD",
    "Denmark": "DNK",
    "Djibouti": "DJI",
    "Dominica": "DMA",
    "Dominican Republic": "DOM",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "El Salvador": "SLV",
    "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI",
    "Estonia": "EST",
    "Eswatini": "SWZ",
    "Ethiopia": "ETH",
    "Fiji": "FJI",
    "Finland": "FIN",
    "France": "FRA",
    "Gabon": "GAB",
    "Gambia": "GMB",
    "Georgia": "GEO",
    "Germany": "DEU",
    "Ghana": "GHA",
    "Greece": "GRC",
    "Grenada": "GRD",
    "Guatemala": "GTM",
    "Guinea": "GIN",
    "Guinea-Bissau": "GNB",
    "Guyana": "GUY",
    "Haiti": "HTI",
    "Honduras": "HND",
    "Hungary": "HUN",
    "Iceland": "ISL",
    "India": "IND",
    "Indonesia": "IDN",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Ireland": "IRL",
    "Israel": "ISR",
    "Italy": "ITA",
    "Jamaica": "JAM",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Kazakhstan": "KAZ",
    "Kenya": "KEN",
    "Kiribati": "KIR",
    "Korea, North": "PRK",
    "Korea, South": "KOR",
    "Kuwait": "KWT",
    "Kyrgyzstan": "KGZ",
    "Laos": "LAO",
    "Latvia": "LVA",
    "Lebanon": "LBN",
    "Lesotho": "LSO",
    "Liberia": "LBR",
    "Libya": "LBY",
    "Liechtenstein": "LIE",
    "Lithuania": "LTU",
    "Luxembourg": "LUX",
    "Madagascar": "MDG",
    "Malawi": "MWI",
    "Malaysia": "MYS",
    "Maldives": "MDV",
    "Mali": "MLI",
    "Malta": "MLT",
    "Marshall Islands": "MHL",
    "Mauritania": "MRT",
    "Mauritius": "MUS",
    "Mexico": "MEX",
    "Micronesia": "FSM",
    "Moldova": "MDA",
    "Monaco": "MCO",
    "Mongolia": "MNG",
    "Montenegro": "MNE",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Myanmar": "MMR",
    "Namibia": "NAM",
    "Nauru": "NRU",
    "Nepal": "NPL",
    "Netherlands": "NLD",
    "New Zealand": "NZL",
    "Nicaragua": "NIC",
    "Niger": "NER",
    "Nigeria": "NGA",
    "North Macedonia": "MKD",
    "Norway": "NOR",
    "Oman": "OMN",
    "Pakistan": "PAK",
    "Palau": "PLW",
    "Palestine": "PSE",
    "Panama": "PAN",
    "Papua New Guinea": "PNG",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Portugal": "PRT",
    "Qatar": "QAT",
    "Romania": "ROU",
    "Russia": "RUS",
    "Rwanda": "RWA",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT",
    "Samoa": "WSM",
    "San Marino": "SMR",
    "Sao Tome and Principe": "STP",
    "Saudi Arabia": "SAU",
    "Senegal": "SEN",
    "Republic of Serbia": "SRB",
    "Seychelles": "SYC",
    "Sierra Leone": "SLE",
    "Singapore": "SGP",
    "Slovakia": "SVK",
    "Slovenia": "SVN",
    "Solomon Islands": "SLB",
    "Somalia": "SOM",
    "South Africa": "ZAF",
    "South Sudan": "SSD",
    "Spain": "ESP",
    "Sri Lanka": "LKA",
    "Sudan": "SDN",
    "Suriname": "SUR",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Syria": "SYR",
    "Taiwan": "TWN",
    "Tajikistan": "TJK",
    "United Republic of Tanzania": "TZA",
    "Thailand": "THA",
    "Timor-Leste": "TLS",
    "Togo": "TGO",
    "Tonga": "TON",
    "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Turkmenistan": "TKM",
    "Tuvalu": "TUV",
    "Uganda": "UGA",
    "Ukraine": "UKR",
    "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
    "United States of America": "USA",
    "Uruguay": "URY",
    "Uzbekistan": "UZB",
    "Vanuatu": "VUT",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
    "Yemen": "YEM",
    "Zambia": "ZMB",
    "Zimbabwe": "ZWE",
    "Greenland": "GRL",
    "French Southern and Antarctic Lands": "ATF"
}


def fetch_api_ninjas_data(url, year_filter, api_field, indicator_key):
    logging.debug(f"Request to API Ninjas: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        req_year = int(year_filter)
        features = []
        # Обробка для населення
        if indicator_key == "population" and isinstance(data, dict) and (
                "historical_population" in data or "population_forecast" in data):
            logging.debug(f"Population API response for year {req_year}: {json.dumps(data, ensure_ascii=False)}")
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
                        pop_val = entry.get(api_field)
                        if pop_val is not None:
                            try:
                                pop_val = float(pop_val)
                            except Exception:
                                pop_val = None
                        # --- Визначаємо ISO-код країни ---
                        country_name = data.get("country_name") or entry.get("country")
                        iso_code = COUNTRY_NAME_TO_ISO.get(country_name, country_name)
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "source": "api_ninjas",
                                "country": iso_code,
                                "year": entry.get("year"),
                                api_field: pop_val
                            },
                            "geometry": None
                        })
                except (ValueError, TypeError):
                    continue
        # Обробка для безробіття та інших випадків (масив відповіді)
        elif isinstance(data, list):
            for entry in data:
                try:
                    if int(entry.get("year", 0)) == req_year:
                        val = entry.get(api_field)
                        # Спробуємо перетворити на float, якщо це можливо
                        if val is not None:
                            try:
                                val = float(val)
                            except Exception:
                                pass
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "source": "api_ninjas",
                                "country": entry.get("country"),
                                "year": entry.get("year"),
                                api_field: val
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
        json_filename = INPUT_GEOJSON
    else:
        json_filename = os.path.join("data", f"api_ninjas_all_{indicator_key}_{year_input}.geojson")
        if os.path.exists(json_filename):
            with open(json_filename, "r", encoding="utf-8") as f:
                fc = json.load(f)
            logging.info(f"Using cached aggregated data from {json_filename}")
        else:
            features_all = []
            for iso in ALL_ISO_CODES:
                if indicator_key == "population":
                    # Для population — тільки по англійській назві
                    eng_name = None
                    for name, code in COUNTRY_NAME_TO_ISO.items():
                        if code == iso:
                            eng_name = name
                            break
                    if eng_name:
                        encoded_country_name = urllib.parse.quote(eng_name)
                        ninjas_url_name = f"{config['api_ninjas_url']}?country={encoded_country_name}"
                        features = fetch_api_ninjas_data(ninjas_url_name, year_input, config["api_field"], indicator_key)
                        # Якщо знайдено — підставляємо ISO-код у properties
                        for f in features:
                            f["properties"]["country"] = iso
                        features_all.extend(features)
                else:
                    # Для unemployment — ISO, потім англійська назва
                    encoded_country_iso = urllib.parse.quote(iso)
                    ninjas_url_iso = f"{config['api_ninjas_url']}?country={encoded_country_iso}"
                    features = fetch_api_ninjas_data(ninjas_url_iso, year_input, config["api_field"], indicator_key)
                    if not features:
                        eng_name = None
                        for name, code in COUNTRY_NAME_TO_ISO.items():
                            if code == iso:
                                eng_name = name
                                break
                        if eng_name:
                            encoded_country_name = urllib.parse.quote(eng_name)
                            ninjas_url_name = f"{config['api_ninjas_url']}?country={encoded_country_name}"
                            features = fetch_api_ninjas_data(ninjas_url_name, year_input, config["api_field"], indicator_key)
                            for f in features:
                                f["properties"]["country"] = iso
                    features_all.extend(features)
            fc = {"type": "FeatureCollection", "features": features_all}
        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(fc, f, ensure_ascii=False, indent=2)
            logging.info(f"API Ninjas data for all countries saved to {json_filename}")
        except Exception as e:
            logging.error(f"Error saving all-countries data: {e}")
        try:
            with open(INPUT_GEOJSON, "w", encoding="utf-8") as f:
                json.dump(fc, f, ensure_ascii=False, indent=2)
            logging.info(f"Aggregated data also copied to {INPUT_GEOJSON}")
        except Exception as e:
            logging.error(f"Error saving input GeoJSON copy: {e}")

    # --- Додаємо фічі для всіх країн, навіть якщо даних немає ---
    features_by_iso = {str(f.get('properties', {}).get('country')).upper(): f for f in fc.get('features', []) if f.get('properties', {}).get('country')}
    completed_features = []
    for iso in ALL_ISO_CODES:
        feat = features_by_iso.get(iso)
        if feat:
            completed_features.append(feat)
        else:
            completed_features.append({
                "type": "Feature",
                "properties": {
                    "source": "no_data",
                    "country": iso,
                    "year": year_input,
                    config["api_field"]: None
                },
                "geometry": None
            })
    fc["features"] = completed_features

    os.makedirs("data", exist_ok=True)
    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
        logging.info(f"GeoJSON written to {json_filename} with {len(fc.get('features', []))} features.")
    except Exception as e:
        logging.error(f"Error saving GeoJSON: {e}")

    cache_data = {"worldbank": {}, "api_ninjas": {}}
    for iso in ALL_ISO_CODES:
        key = f"{indicator_key}_{iso}_{year_input}"
        # Шукаємо фічу для цієї країни
        feat = next((f for f in fc["features"] if str(f.get("properties", {}).get("country")).upper() == iso), None)
        field_val = None
        if feat:
            field_val = feat.get("properties", {}).get(config["api_field"])
        # Визначаємо джерело
        if int(year_input) <= 2023:
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
