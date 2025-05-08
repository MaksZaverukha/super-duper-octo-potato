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
import time

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Файл для запису вхідного GeoJSON (для сумісності з іншими модулями, наприклад, qgis_processor.py)
INPUT_GEOJSON = os.path.join("data", "input.geojson")

DATACOMMONS_API_KEY = os.environ.get("DATACOMMONS_API_KEY", "")
DATACOMMONS_API_URL = "https://api.datacommons.org/v2/"  # REST v2

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country"
PER_PAGE = 1000

# --- Шлях для всіх даних ---
DATA_DIR = os.path.join("data", "worldbank")
os.makedirs(DATA_DIR, exist_ok=True)

INDICATORS = {
    "unemployment": {
        "name": "Рівень безробіття",
        "sources": [
            {"type": "worldbank", "indicator": "SL.UEM.TOTL.ZS", "api_field": "unemployment_rate"},
            {"type": "owid", "file": "owid_unemployment.csv", "api_field": "unemployment_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_unemployment_rate", "api_field": "unemployment_rate"}
        ]
    },
    "population": {
        "name": "Населення",
        "sources": [
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
    "energy_use": {
        "name": "Використання енергії (кг нафтового еквіваленту на особу)",
        "sources": [
            {"type": "worldbank", "indicator": "EG.USE.PCAP.KG.OE", "api_field": "energy_use"},
            {"type": "owid", "file": "owid_energy.csv", "api_field": "energy_use"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_energy_consumption_per_capita", "api_field": "energy_use"}
        ]
    },
    "urbanization_rate": {
        "name": "Рівень урбанізації (%)",
        "sources": [
            {"type": "worldbank", "indicator": "SP.URB.TOTL.IN.ZS", "api_field": "urbanization_rate"},
            {"type": "owid", "file": "owid_urbanization.csv", "api_field": "urbanization_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_urbanization_rate", "api_field": "urbanization_rate"}
        ]
    },
    "gdp": {
        "name": "Валовий внутрішній продукт (ВВП)",
        "sources": [
            {"type": "worldbank", "indicator": "NY.GDP.MKTP.CD", "api_field": "gdp"},
            {"type": "owid", "file": "owid_gdp.csv", "api_field": "gdp"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)", "api_field": "gdp"}
        ]
    },
    "gdp_per_capita": {
        "name": "ВВП на душу населення",
        "sources": [
            {"type": "worldbank", "indicator": "NY.GDP.PCAP.CD", "api_field": "gdp_per_capita"},
            {"type": "owid", "file": "owid_gdp_per_capita.csv", "api_field": "gdp_per_capita"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita", "api_field": "gdp_per_capita"}
        ]
    },
    "inflation": {
        "name": "Інфляція, %",
        "sources": [
            {"type": "worldbank", "indicator": "FP.CPI.TOTL.ZG", "api_field": "inflation_rate"},
            {"type": "owid", "file": "owid_inflation.csv", "api_field": "inflation_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_inflation_rate", "api_field": "inflation_rate"}
        ]
    },
    "life_expectancy": {
        "name": "Тривалість життя",
        "sources": [
            {"type": "worldbank", "indicator": "SP.DYN.LE00.IN", "api_field": "life_expectancy"},
            {"type": "owid", "file": "owid_life_expectancy.csv", "api_field": "life_expectancy"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_life_expectancy", "api_field": "life_expectancy"}
        ]
    },
    "literacy_rate": {
        "name": "Рівень грамотності",
        "sources": [
            {"type": "worldbank", "indicator": "SE.ADT.LITR.ZS", "api_field": "literacy_rate"},
            {"type": "owid", "file": "owid_literacy_rate.csv", "api_field": "literacy_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_literacy_rate", "api_field": "literacy_rate"}
        ]
    },
    "poverty_rate": {
        "name": "Рівень бідності",
        "sources": [
            {"type": "worldbank", "indicator": "SI.POV.DDAY", "api_field": "poverty_rate"},
            {"type": "owid", "file": "owid_poverty_rate.csv", "api_field": "poverty_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_percentage_of_population_living_in_poverty", "api_field": "poverty_rate"}
        ]
    },
    "urban_population": {
        "name": "Міське населення",
        "sources": [
            {"type": "worldbank", "indicator": "SP.URB.TOTL.IN.ZS", "api_field": "urban_population"},
            {"type": "owid", "file": "owid_urban_population.csv", "api_field": "urban_population"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_urban_population", "api_field": "urban_population"}
        ]
    },
    "birth_rate": {
        "name": "Народжуваність (на 1000)",
        "sources": [
            {"type": "worldbank", "indicator": "SP.DYN.CBRT.IN", "api_field": "birth_rate"},
            {"type": "owid", "file": "owid_birth_rate.csv", "api_field": "birth_rate"},
            {"type": "wikipedia", "url": "https://en.wikipedia.org/wiki/List_of_countries_by_birth_rate", "api_field": "birth_rate"}
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
    # Energy use per capita (World Bank, актуальний датасет)
    "energy_use": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/energy_use_per_capita/energy_use_per_capita.csv",
    # Urbanization rate (World Bank, актуальний датасет)
    "urbanization_rate": "https://raw.githubusercontent.com/owid/owid-grapher-data/master/ETL/urban_population_percent/urban_population_percent.csv"
}

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


def fetch_indicator_data_fallback(indicator_key, year_input, force_refresh=False):
    cache_path = os.path.join(DATA_DIR, f"{indicator_key}_{year_input}.json")
    if force_refresh and os.path.exists(cache_path):
        os.remove(cache_path)
    result = {iso: None for iso in ALL_ISO_CODES}
    sources = INDICATORS[indicator_key]["sources"]
    # --- Збираємо дані з усіх джерел, але якщо є WorldBank — він має пріоритет для відсутніх значень ---
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
                years = country_years.get(iso, {})
                if int(year_input) in years and years[int(year_input)] is not None:
                    result[iso] = years[int(year_input)]
    # --- Далі інші джерела, але не перезаписуємо те, що вже є з WorldBank ---
    for src in sources:
        if src["type"] == "worldbank":
            continue
        elif src["type"] == "owid" or src["type"] == "wikipedia":
            csv_path = os.path.join(DATA_DIR, src["file"] if "file" in src else f"wikipedia_{indicator_key}.csv")
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
                    if int(year_input) in years and years[int(year_input)] is not None:
                        result[iso] = years[int(year_input)]
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def check_owid_years(file_path):
    """
    Виводить у лог всі роки, які є у CSV-файлі OWID для перевірки актуальності.
    """
    if not os.path.exists(file_path):
        logging.warning(f"OWID CSV {file_path} не знайдено для перевірки років.")
        return
    years = set()
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                year = int(row.get("year", "0"))
                years.add(year)
            except Exception:
                continue
    if years:
        logging.info(f"OWID CSV {os.path.basename(file_path)} має дані за роки: {sorted(years)}")
    else:
        logging.warning(f"OWID CSV {os.path.basename(file_path)} не містить жодного року.")

# --- Далі код для генерації GeoJSON та запуску з консолі ---
def generate_geojson(indicator_key, country_input=None, year_input=None, force_refresh=False):
    if indicator_key not in INDICATORS:
        logging.error("Invalid indicator!")
        return
    config = INDICATORS[indicator_key]
    logging.info(f"Loading data for {config['name']}")
    if year_input is None:
        year_input = "2023"
    # --- Додатково: перевірка OWID-файлу на наявність потрібних років ---
    for src in INDICATORS[indicator_key]["sources"]:
        if src["type"] == "owid":
            csv_path = os.path.join(DATA_DIR, src["file"])
            # Завантажити файл, якщо треба
            if not os.path.exists(csv_path):
                url = OWID_CSV_URLS.get(indicator_key)
                if url:
                    download_owid_csv_if_needed(src["file"], url)
            check_owid_years(csv_path)
    # --- Fallback: отримуємо дані для всіх країн за діапазон років ---
    try:
        year_int = int(year_input)
    except Exception:
        year_int = 2023
    years_range = [str(y) for y in range(year_int - 5, year_int + 1) if y >= 1980]
    all_iso_to_value = {}
    for y in years_range:
        all_iso_to_value[y] = fetch_indicator_data_fallback(indicator_key, y, force_refresh=force_refresh)
    # --- Формуємо features та зберігаємо geojson для кожного року з діапазону ---
    for y in years_range:
        iso_to_value = all_iso_to_value[y]
        features = []
        for iso in ALL_ISO_CODES:
            val = iso_to_value.get(iso)
            features.append({
                "type": "Feature",
                "properties": {
                    "source": "fallback",
                    "country": iso,
                    "year": y,
                    config["sources"][0]["api_field"]: val
                },
                "geometry": None
            })
        fc = {"type": "FeatureCollection", "features": features}
        json_filename = os.path.join(DATA_DIR, f"{indicator_key}_{y}.geojson")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
    # --- Далі як було: копія для input.geojson та кеш ---
    iso_to_value = all_iso_to_value[str(year_int)]
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
    # --- Формуємо кеш для фронтенду: всі роки з діапазону ---
    cache_data = {"worldbank": {}}
    for y in years_range:
        for iso in ALL_ISO_CODES:
            key = f"{indicator_key}_{iso}_{y}"
            field_val = all_iso_to_value[y].get(iso)
            cache_data["worldbank"][key] = field_val
    try:
        with open(os.path.join("static", "data_cache.json"), "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logging.info("Cache updated: static/data_cache.json")
    except Exception as e:
        logging.error(f"Error saving cache: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--auto":
        # Додаємо force_refresh для примусового оновлення
        generate_geojson(sys.argv[2], sys.argv[3], sys.argv[4], force_refresh=True)
    else:
        logging.info("Available indicators:")
        for key, value in INDICATORS.items():
            logging.info(f"{key}: {value['name']}")
        selected_indicator = input("Indicator (population or unemployment): ").strip()
        selected_country = input("Country (for years > 2023, e.g., Kazakhstan): ").strip()
        year_selected = input("Year: ").strip()
        generate_geojson(selected_indicator, selected_country, year_selected)
