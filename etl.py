#!/usr/bin/env python
import os
import json
import requests
import logging
import xml.etree.ElementTree as ET
import sys
import urllib.parse
import shutil  # Для копіювання файлів
import csv

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Файл для запису вхідного GeoJSON (для сумісності з іншими модулями, наприклад, qgis_processor.py)
INPUT_GEOJSON = os.path.join("data", "input.geojson")

API_KEY = "5V7O0c43JxoQZRUQtqla3Q==xfXFKSRNZW0CR5jj"
HEADERS = {"X-Api-Key": API_KEY}

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country"
PER_PAGE = 1000

# --- Шлях для всіх даних ---
DATA_DIR = os.path.join("data", "worldbank")
os.makedirs(DATA_DIR, exist_ok=True)

INDICATORS = {
    "unemployment": {
        "name": "Рівень безробіття",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/unemployment", "api_field": "unemployment_rate"},
            {"type": "worldbank", "indicator": "SL.UEM.TOTL.ZS", "api_field": "unemployment_rate"},
            {"type": "owid", "file": "owid_unemployment.csv", "api_field": "unemployment_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_unemployment_rate", "api_field": "unemployment_rate"}
        ]
    },
    "population": {
        "name": "Населення",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/population", "api_field": "population"},
            {"type": "worldbank", "indicator": "SP.POP.TOTL", "api_field": "population"},
            {"type": "owid", "file": "owid_population.csv", "api_field": "population"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population", "api_field": "population"}
        ]
    },
    "median_age": {
        "name": "Медіанний вік",
        "sources": [
            {"type": "owid", "file": "owid_median_age.csv", "api_field": "median_age"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_median_age", "api_field": "median_age"}
        ]
    },
    "internet_users": {
        "name": "Користувачі Інтернету (%)",
        "sources": [
            {"type": "worldbank", "indicator": "IT.NET.USER.ZS", "api_field": "internet_users"},
            {"type": "owid", "file": "owid_internet.csv", "api_field": "internet_users"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_number_of_Internet_users", "api_field": "internet_users"}
        ]
    },
    "mobile_subscriptions": {
        "name": "Мобільні підписки (на 100 осіб)",
        "sources": [
            {"type": "worldbank", "indicator": "IT.CEL.SETS.P2", "api_field": "mobile_subscriptions"},
            {"type": "owid", "file": "owid_mobile.csv", "api_field": "mobile_subscriptions"}
        ]
    },
    "poverty_gap": {
        "name": "Розрив бідності (%)",
        "sources": [
            {"type": "worldbank", "indicator": "SI.POV.GAPS", "api_field": "poverty_gap"},
            {"type": "owid", "file": "owid_poverty_gap.csv", "api_field": "poverty_gap"}
        ]
    },
    "health_expenditure": {
        "name": "Витрати на здоров'я (% ВВП)",
        "sources": [
            {"type": "worldbank", "indicator": "SH.XPD.CHEX.GD.ZS", "api_field": "health_expenditure"},
            {"type": "owid", "file": "owid_health_expenditure.csv", "api_field": "health_expenditure"}
        ]
    },
    "school_enrollment": {
        "name": "Охоплення школою (%)",
        "sources": [
            {"type": "worldbank", "indicator": "SE.PRM.NENR", "api_field": "school_enrollment"},
            {"type": "owid", "file": "owid_school_enrollment.csv", "api_field": "school_enrollment"}
        ]
    },
    "homicide_rate": {
        "name": "Рівень вбивств (на 100 тис.)",
        "sources": [
            {"type": "worldbank", "indicator": "VC.IHR.PSRC.P5", "api_field": "homicide_rate"},
            {"type": "owid", "file": "owid_homicide.csv", "api_field": "homicide_rate"}
        ]
    },
    "co2_emissions": {
        "name": "Викиди CO₂ (тонн на особу)",
        "sources": [
            {"type": "worldbank", "indicator": "EN.ATM.CO2E.PC", "api_field": "co2_emissions"},
            {"type": "owid", "file": "owid_co2.csv", "api_field": "co2_emissions"}
        ]
    },
    "energy_use": {
        "name": "Використання енергії (кг нафтового еквіваленту на особу)",
        "sources": [
            {"type": "worldbank", "indicator": "EG.USE.PCAP.KG.OE", "api_field": "energy_use"},
            {"type": "owid", "file": "owid_energy.csv", "api_field": "energy_use"}
        ]
    },
    "urbanization_rate": {
        "name": "Рівень урбанізації (%)",
        "sources": [
            {"type": "worldbank", "indicator": "SP.URB.TOTL.IN.ZS", "api_field": "urbanization_rate"},
            {"type": "owid", "file": "owid_urbanization.csv", "api_field": "urbanization_rate"}
        ]
    },
    "gdp": {
        "name": "Валовий внутрішній продукт (ВВП)",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/gdp", "api_field": "gdp"},
            {"type": "worldbank", "indicator": "NY.GDP.MKTP.CD", "api_field": "gdp"}
        ]
    },
    "gdp_per_capita": {
        "name": "ВВП на душу населення",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/gdp_per_capita", "api_field": "gdp_per_capita"},
            {"type": "worldbank", "indicator": "NY.GDP.PCAP.CD", "api_field": "gdp_per_capita"}
        ]
    },
    "inflation": {
        "name": "Інфляція, %",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/inflation", "api_field": "inflation_rate"},
            {"type": "worldbank", "indicator": "FP.CPI.TOTL.ZG", "api_field": "inflation_rate"}
        ]
    },
    "life_expectancy": {
        "name": "Тривалість життя",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/lifeexpectancy", "api_field": "life_expectancy"},
            {"type": "worldbank", "indicator": "SP.DYN.LE00.IN", "api_field": "life_expectancy"}
        ]
    },
    "literacy_rate": {
        "name": "Рівень грамотності",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/literacy", "api_field": "literacy_rate"},
            {"type": "worldbank", "indicator": "SE.ADT.LITR.ZS", "api_field": "literacy_rate"}
        ]
    },
    "poverty_rate": {
        "name": "Рівень бідності",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/povertyrate", "api_field": "poverty_rate"},
            {"type": "worldbank", "indicator": "SI.POV.DDAY", "api_field": "poverty_rate"}
        ]
    },
    "urban_population": {
        "name": "Міське населення",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/urbanpopulation", "api_field": "urban_population"},
            {"type": "worldbank", "indicator": "SP.URB.TOTL.IN.ZS", "api_field": "urban_population"}
        ]
    },
    "birth_rate": {
        "name": "Народжуваність (на 1000)",
        "sources": [
            {"type": "api_ninjas", "url": "https://api.api-ninjas.com/v1/birthrate", "api_field": "birth_rate"},
            {"type": "worldbank", "indicator": "SP.DYN.CBRT.IN", "api_field": "birth_rate"}
        ]
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

def download_owid_csv_if_needed(file_name, url):
    """
    Завантажує CSV з OWID у data/worldbank, якщо його ще немає.
    """
    file_path = os.path.join(DATA_DIR, file_name)
    if os.path.exists(file_path):
        return file_path
    try:
        logging.info(f"Завантаження {file_name} з {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(r.content)
        logging.info(f"CSV {file_name} завантажено у {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Не вдалося завантажити {file_name}: {e}")
        return None

# --- OWID CSV URL для кожного показника (оновіть за потреби) ---
# Нові посилання беруться з https://github.com/owid/owid-datasets/tree/master/datasets або https://github.com/owid/owid-grapher-data/tree/master/ETL
OWID_CSV_URLS = {
    # Median age (UN, актуальний датасет)
    "median_age": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/median_age/median_age.csv",
    # Internet users (World Bank, актуальний датасет)
    "internet_users": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/internet_users/internet_users.csv",
    # Mobile subscriptions (World Bank, актуальний датасет)
    "mobile_subscriptions": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/mobile_cellular_subscriptions/mobile_cellular_subscriptions.csv",
    # Poverty gap (World Bank, актуальний датасет)
    "poverty_gap": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/poverty_gap_at_1.90_a_day/poverty_gap_at_1.90_a_day.csv",
    # Health expenditure (World Bank, актуальний датасет)
    "health_expenditure": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/health_expenditure_percent_gdp/health_expenditure_percent_gdp.csv",
    # School enrollment (World Bank, актуальний датасет)
    "school_enrollment": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/school_enrollment_primary_gross/school_enrollment_primary_gross.csv",
    # Homicide rate (World Bank, актуальний датасет)
    "homicide_rate": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/homicide_rate/homicide_rate.csv",
    # CO2 emissions per capita (OWID, актуальний датасет)
    "co2_emissions": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/co2_emissions_per_capita/co2_emissions_per_capita.csv",
    # Energy use per capita (World Bank, актуальний датасет)
    "energy_use": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/energy_use_per_capita/energy_use_per_capita.csv",
    # Urbanization rate (World Bank, актуальний датасет)
    "urbanization_rate": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/urban_population_percent/urban_population_percent.csv"
}

def fetch_api_ninjas_data(url, year_filter, api_field, indicator_key):
    logging.debug(f"Request to API Ninjas: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        req_year = int(year_filter)
        features = []
        # --- Оновлена логіка для населення ---
        if indicator_key == "population" and isinstance(data, dict) and (
                "historical_population" in data or "population_forecast" in data):
            logging.debug(f"Population API response for year {req_year}: {json.dumps(data, ensure_ascii=False)}")
            arr = []
            # Для 2025 — population_forecast[0], для 2024 — population_forecast[1]
            if req_year == 2025 and "population_forecast" in data and len(data["population_forecast"]) > 0:
                arr = [data["population_forecast"][0]]
            elif req_year == 2024 and "population_forecast" in data and len(data["population_forecast"]) > 1:
                arr = [data["population_forecast"][1]]
            elif "historical_population" in data:
                # Для попередніх років — шукаємо точний рік або останній доступний
                arr = [entry for entry in data["historical_population"] if int(entry.get("year", 0)) == req_year]
                if not arr and len(data["historical_population"]) > 0:
                    arr = [data["historical_population"][-1]]
            elif "population_forecast" in data and len(data["population_forecast"]) > 0:
                arr = [data["population_forecast"][0]]
            else:
                logging.info(f"No population records found for year {req_year} in API Ninjas response.")
            for entry in arr:
                try:
                    pop_val = entry.get(api_field)
                    if pop_val is not None:
                        try:
                            pop_val = float(pop_val)
                        except Exception:
                            pop_val = None
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
        elif isinstance(data, list):
            for entry in data:
                try:
                    if int(entry.get("year", 0)) == req_year:
                        val = entry.get(api_field)
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
    file_name = f"worldbank_{indicator}_{year_filter}.xml"
    file_path = os.path.join(DATA_DIR, file_name)
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


def fetch_indicator_data_fallback(indicator_key, year_input):
    """
    Повертає словник {ISO: value} для всіх країн по заданому показнику і року,
    fallback: шукає найближчий попередній рік у кожному джерелі для кожної країни.
    """
    cache_path = os.path.join(DATA_DIR, f"{indicator_key}_{year_input}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            result = json.load(f)
    else:
        result = {iso: None for iso in ALL_ISO_CODES}
    sources = INDICATORS[indicator_key]["sources"]
    updated = False
    for src in sources:
        # --- WorldBank ---
        if src["type"] == "worldbank":
            file_path = download_and_save_worldbank_xml(src["indicator"], year_input)
            if not file_path:
                continue
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
            except Exception as e:
                logging.error(f"Error parsing World Bank XML: {e}")
                continue
            country_years = {}
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
                if rec_country is None or rec_year is None or rec_value is None:
                    continue
                if rec_country not in country_years:
                    country_years[rec_country] = {}
                country_years[rec_country][rec_year] = rec_value
            for iso in result:
                if result[iso] is not None:
                    continue
                years = country_years.get(iso, {})
                # --- шукаємо найближчий рік ≤ обраного ---
                prev_years = [y for y in years if y <= int(year_input) and years[y] is not None]
                if prev_years:
                    best_year = max(prev_years)
                    result[iso] = years[best_year]
                    updated = True
        # --- OWID ---
        elif src["type"] == "owid":
            csv_path = os.path.join(DATA_DIR, src["file"])
            if os.path.exists(csv_path):
                country_years = {}
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        iso = row.get("iso_code", "").upper()
                        try:
                            year = int(row.get("year", "0"))
                        except Exception:
                            continue
                        v = row.get(src["api_field"])
                        if v is not None and v != "":
                            try:
                                value = float(v)
                            except Exception:
                                value = v
                            if iso not in country_years:
                                country_years[iso] = {}
                            country_years[iso][year] = value
                for iso in result:
                    if result[iso] is not None:
                        continue
                    years = country_years.get(iso, {})
                    prev_years = [y for y in years if y <= int(year_input) and years[y] is not None]
                    if prev_years:
                        best_year = max(prev_years)
                        result[iso] = years[best_year]
                        updated = True
        # --- wikipedia ---
        elif src["type"] == "wikipedia":
            csv_path = os.path.join(DATA_DIR, f"wikipedia_{indicator_key}.csv")
            if os.path.exists(csv_path):
                country_years = {}
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        iso = row.get("iso_code", "").upper()
                        try:
                            year = int(row.get("year", "0"))
                        except Exception:
                            continue
                        v = row.get(src["api_field"])
                        if v is not None and v != "":
                            try:
                                value = float(v)
                            except Exception:
                                value = v
                            if iso not in country_years:
                                country_years[iso] = {}
                            country_years[iso][year] = value
                for iso in result:
                    if result[iso] is not None:
                        continue
                    years = country_years.get(iso, {})
                    prev_years = [y for y in years if y <= int(year_input) and years[y] is not None]
                    if prev_years:
                        best_year = max(prev_years)
                        result[iso] = years[best_year]
                        updated = True
        # --- api_ninjas ---
        elif src["type"] == "api_ninjas":
            features = fetch_api_ninjas_data(src["url"], year_input, src["api_field"], indicator_key)
            country_years = {}
            for feat in features:
                iso = feat["properties"].get("country", "").upper()
                year = feat["properties"].get("year")
                try:
                    year = int(year)
                except Exception:
                    continue
                val = feat["properties"].get(src["api_field"])
                if val is not None:
                    if iso not in country_years:
                        country_years[iso] = {}
                    country_years[iso][year] = val
            for iso in result:
                if result[iso] is not None:
                    continue
                years = country_years.get(iso, {})
                prev_years = [y for y in years if y <= int(year_input) and years[y] is not None]
                if prev_years:
                    best_year = max(prev_years)
                    result[iso] = years[best_year]
                    updated = True
    if updated:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result

# --- Далі код для генерації GeoJSON та запуску з консолі ---
def generate_geojson(indicator_key, country_input=None, year_input=None):
    if indicator_key not in INDICATORS:
        logging.error("Invalid indicator!")
        return
    config = INDICATORS[indicator_key]
    logging.info(f"Loading data for {config['name']}")
    if year_input is None:
        year_input = "2025"
    # --- Fallback: отримуємо дані для всіх країн ---
    iso_to_value = fetch_indicator_data_fallback(indicator_key, year_input)
    features = []
    for iso in ALL_ISO_CODES:
        val = iso_to_value.get(iso)
        features.append({
            "type": "Feature",
            "properties": {
                "source": "fallback",
                "country": iso,
                "year": year_input,
                config["sources"][0]["api_field"]: val
            },
            "geometry": None
        })
    fc = {"type": "FeatureCollection", "features": features}
    json_filename = os.path.join(DATA_DIR, f"{indicator_key}_{year_input}.geojson")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    try:
        with open(INPUT_GEOJSON, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
        logging.info(f"Aggregated data also copied to {INPUT_GEOJSON}")
    except Exception as e:
        logging.error(f"Error saving input GeoJSON copy: {e}")
    cache_data = {"worldbank": {}, "api_ninjas": {}}
    for iso in ALL_ISO_CODES:
        key = f"{indicator_key}_{iso}_{year_input}"
        field_val = iso_to_value.get(iso)
        cache_data["worldbank"][key] = field_val
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
