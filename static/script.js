document.addEventListener("DOMContentLoaded", function() {
    // --- Глобальні змінні та DOM ---
    let currentCache = {};
    let currentIndicator = document.getElementById('indicatorSelect').value;
    let currentYear = document.getElementById('yearSlider').value;
    let boundariesLayer;
    let finalLayer;

    const countryInput = document.getElementById('countryInput');
    const countryDatalist = document.getElementById('countryList');
    const indicatorSelect = document.getElementById('indicatorSelect');
    const yearSlider = document.getElementById('yearSlider');
    const yearDisplay = document.getElementById('yearDisplay');
    const infoPanel = document.getElementById('infoPanel');

    // --- Country mapping ---
    const countryMapping = {
        "AFG": "Afghanistan",
        "ALB": "Albania",
        "DZA": "Algeria",
        "AND": "Andorra",
        "AGO": "Angola",
        "ARG": "Argentina",
        "ARM": "Armenia",
        "AUS": "Australia",
        "AUT": "Austria",
        "AZE": "Azerbaijan",
        "BHS": "Bahamas",
        "BHR": "Bahrain",
        "BGD": "Bangladesh",
        "BRB": "Barbados",
        "BLR": "Belarus",
        "BEL": "Belgium",
        "BLZ": "Belize",
        "BEN": "Benin",
        "BTN": "Bhutan",
        "BOL": "Bolivia",
        "BIH": "Bosnia and Herzegovina",
        "BWA": "Botswana",
        "BRA": "Brazil",
        "BRN": "Brunei Darussalam",
        "BGR": "Bulgaria",
        "BFA": "Burkina Faso",
        "BDI": "Burundi",
        "KHM": "Cambodia",
        "CMR": "Cameroon",
        "CAN": "Canada",
        "CPV": "Cape Verde",
        "CAF": "Central African Republic",
        "TCD": "Chad",
        "CHL": "Chile",
        "CHN": "China",
        "COL": "Colombia",
        "COM": "Comoros",
        "COG": "Congo",
        "CRI": "Costa Rica",
        "CIV": "Ivory Coast",
        "HRV": "Croatia",
        "CUB": "Cuba",
        "CYP": "Cyprus",
        "CZE": "Czechia",
        "COD": "Democratic Republic of the Congo",
        "DNK": "Denmark",
        "DJI": "Djibouti",
        "DMA": "Dominica",
        "DOM": "Dominican Republic",
        "ECU": "Ecuador",
        "EGY": "Egypt",
        "SLV": "El Salvador",
        "GNQ": "Equatorial Guinea",
        "ERI": "Eritrea",
        "EST": "Estonia",
        "SWZ": "Eswatini",
        "ETH": "Ethiopia",
        "FJI": "Fiji",
        "FIN": "Finland",
        "FRA": "France",
        "GAB": "Gabon",
        "GMB": "Gambia",
        "GEO": "Georgia",
        "DEU": "Germany",
        "GHA": "Ghana",
        "GRC": "Greece",
        "GRD": "Grenada",
        "GTM": "Guatemala",
        "GIN": "Guinea",
        "GNB": "Guinea-Bissau",
        "GUY": "Guyana",
        "HTI": "Haiti",
        "HND": "Honduras",
        "HUN": "Hungary",
        "ISL": "Iceland",
        "IND": "India",
        "IDN": "Indonesia",
        "IRN": "Iran",
        "IRQ": "Iraq",
        "IRL": "Ireland",
        "ISR": "Israel",
        "ITA": "Italy",
        "JAM": "Jamaica",
        "JPN": "Japan",
        "JOR": "Jordan",
        "KAZ": "Kazakhstan",
        "KEN": "Kenya",
        "KIR": "Kiribati",
        "PRK": "Korea, North",
        "KOR": "Korea, South",
        "KWT": "Kuwait",
        "KGZ": "Kyrgyzstan",
        "LAO": "Laos",
        "LVA": "Latvia",
        "LBN": "Lebanon",
        "LSO": "Lesotho",
        "LBR": "Liberia",
        "LBY": "Libya",
        "LIE": "Liechtenstein",
        "LTU": "Lithuania",
        "LUX": "Luxembourg",
        "MDG": "Madagascar",
        "MWI": "Malawi",
        "MYS": "Malaysia",
        "MDV": "Maldives",
        "MLI": "Mali",
        "MLT": "Malta",
        "MHL": "Marshall Islands",
        "MRT": "Mauritania",
        "MUS": "Mauritius",
        "MEX": "Mexico",
        "FSM": "Micronesia",
        "MDA": "Moldova",
        "MCO": "Monaco",
        "MNG": "Mongolia",
        "MNE": "Montenegro",
        "MAR": "Morocco",
        "MOZ": "Mozambique",
        "MMR": "Myanmar",
        "NAM": "Namibia",
        "NRU": "Nauru",
        "NPL": "Nepal",
        "NLD": "Netherlands",
        "NZL": "New Zealand",
        "NIC": "Nicaragua",
        "NER": "Niger",
        "NGA": "Nigeria",
        "MKD": "North Macedonia",
        "NOR": "Norway",
        "OMN": "Oman",
        "PAK": "Pakistan",
        "PLW": "Palau",
        "PSE": "Palestine",
        "PAN": "Panama",
        "PNG": "Papua New Guinea",
        "PRY": "Paraguay",
        "PER": "Peru",
        "PHL": "Philippines",
        "POL": "Poland",
        "PRT": "Portugal",
        "QAT": "Qatar",
        "ROU": "Romania",
        "RUS": "Russia",
        "RWA": "Rwanda",
        "KNA": "Saint Kitts and Nevis",
        "LCA": "Saint Lucia",
        "VCT": "Saint Vincent and the Grenadines",
        "WSM": "Samoa",
        "SMR": "San Marino",
        "STP": "Sao Tome and Principe",
        "SAU": "Saudi Arabia",
        "SEN": "Senegal",
        "SRB": "Republic of Serbia",
        "SYC": "Seychelles",
        "SLE": "Sierra Leone",
        "SGP": "Singapore",
        "SVK": "Slovakia",
        "SVN": "Slovenia",
        "SLB": "Solomon Islands",
        "SOM": "Somalia",
        "ZAF": "South Africa",
        "SSD": "South Sudan",
        "ESP": "Spain",
        "LKA": "Sri Lanka",
        "SDN": "Sudan",
        "SUR": "Suriname",
        "SWE": "Sweden",
        "CHE": "Switzerland",
        "SYR": "Syria",
        "TWN": "Taiwan",
        "TJK": "Tajikistan",
        "TZA": "United Republic of Tanzania",
        "THA": "Thailand",
        "TLS": "Timor-Leste",
        "TGO": "Togo",
        "TON": "Tonga",
        "TTO": "Trinidad and Tobago",
        "TUN": "Tunisia",
        "TUR": "Turkey",
        "TKM": "Turkmenistan",
        "TUV": "Tuvalu",
        "UGA": "Uganda",
        "UKR": "Ukraine",
        "ARE": "United Arab Emirates",
        "GBR": "United Kingdom",
        "USA": "United States of America",
        "URY": "Uruguay",
        "UZB": "Uzbekistan",
        "VUT": "Vanuatu",
        "VEN": "Venezuela",
        "VNM": "Vietnam",
        "YEM": "Yemen",
        "ZMB": "Zambia",
        "ZWE": "Zimbabwe",
        "GRL": "Greenland",
        "ATF": "French Southern and Antarctic Lands",

    };

    // --- Додаткові альтернативні назви для проблемних країн ---
    const alternativeCountryNames = {
        "COD": ["Democratic Republic of the Congo", "Congo, Democratic Republic of the", "Dem. Rep. Congo", "Congo-Kinshasa"],
        "COG": ["Republic of the Congo", "Congo", "Congo-Brazzaville"],
        "KOR": ["South Korea", "Korea, South", "Republic of Korea"],
        "PRK": ["North Korea", "Korea, North", "Democratic People's Republic of Korea"],
        "CIV": ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire"],
        "TZA": ["Tanzania", "United Republic of Tanzania"],
        "GRL": ["Greenland"],
        "IND": ["India"],
        // Додавайте ще за потреби
    };

    function getWorldbankCountry(input) {
        input = input.trim();
        if (input.length === 3 && input === input.toUpperCase() && countryMapping[input]) {
            return input;
        }
        for (let iso in countryMapping) {
            if (countryMapping[iso].toLowerCase() === input.toLowerCase()) {
                return iso;
            }
        }
        if (input.toLowerCase() === "україна") return "UKR";
        for (let iso in countryMapping) {
            if (countryMapping[iso].toLowerCase().includes(input.toLowerCase())) {
                return iso;
            }
        }
        return input;
    }

    function getCountryName(feature) {
        const fields = ["ADMIN", "NAME", "country"];
        for (let field of fields) {
            if (feature.properties && feature.properties[field]) {
                return feature.properties[field].trim();
            }
        }
        return "";
    }

    // --- Функція для отримання ISO-коду країни з geojson feature ---
    function getCountryISOFromFeature(feature) {
        const name = getCountryName(feature).toLowerCase().replace(/[^a-zа-яёіїєґ0-9 ]/gi, '').trim();
        // 1. Точний збіг
        for (const iso in countryMapping) {
            if (countryMapping[iso].toLowerCase() === name) return iso;
        }
        // 2. Частковий збіг (наприклад, Czechia vs Czech Republic)
        for (const iso in countryMapping) {
            if (countryMapping[iso].toLowerCase().includes(name) || name.includes(countryMapping[iso].toLowerCase())) return iso;
        }
        // 3. Якщо не знайдено — null
        return null;
    }

    // --- Функція для пошуку даних по альтернативних назвах ---
    function findValueByAlternativeNames(cache, indicator, year, feature) {
        // 1. Спробувати по ISO-коду
        let iso = getCountryISOFromFeature(feature);
        let keysToTry = [];
        if (iso) {
            keysToTry.push(`${indicator}_${iso}_${year}`);
            if (alternativeCountryNames[iso]) {
                for (let alt of alternativeCountryNames[iso]) {
                    keysToTry.push(`${indicator}_${alt}_${year}`);
                }
            }
        }
        // 2. Спробувати по ADMIN, NAME, BRK_NAME
        const props = feature.properties || {};
        ["ADMIN", "NAME", "BRK_NAME", "NAME_LONG", "NAME_SORT", "NAME_CIAWF"].forEach(field => {
            if (props[field]) {
                keysToTry.push(`${indicator}_${props[field]}_${year}`);
            }
        });
        // 3. Перебрати всі ключі в кеші, які містять назву країни (частковий збіг)
        if (cache) {
            for (let key of Object.keys(cache)) {
                for (let field of ["ADMIN", "NAME", "BRK_NAME", "NAME_LONG", "NAME_SORT", "NAME_CIAWF"]) {
                    if (props[field] && key.toLowerCase().includes(props[field].toLowerCase()) && key.startsWith(`${indicator}_`) && key.endsWith(`_${year}`)) {
                        keysToTry.push(key);
                    }
                }
            }
        }
        // 4. Повернути перше знайдене значення
        for (let key of keysToTry) {
            if (cache && cache[key] !== undefined && cache[key] !== null) {
                return cache[key];
            }
        }
        return null;
    }

    // --- Легенда ---
    const legendConfig = {
        population: {
            colorLow: "#ADD8E6",
            colorHigh: "#00008B",
            label: "Населення"
        },
        unemployment: {
            colorLow: "#edf8e9",
            colorHigh: "#006d2c",
            label: "Рівень безробіття"
        },
        gdp: {
            colorLow: "#f7fcf5",
            colorHigh: "#00441b",
            label: "ВВП"
        },
        gdp_per_capita: {
            colorLow: "#f7fbff",
            colorHigh: "#08306b",
            label: "ВВП на душу"
        },
        inflation: {
            colorLow: "#fff7ec",
            colorHigh: "#7f0000",
            label: "Інфляція, %"
        },
        life_expectancy: {
            colorLow: "#f7fcfd",
            colorHigh: "#004b6f",
            label: "Тривалість життя"
        },
        literacy_rate: {
            colorLow: "#f7fcf0",
            colorHigh: "#00441b",
            label: "Грамотність"
        },
        poverty_rate: {
            colorLow: "#fff5f0",
            colorHigh: "#67000d",
            label: "Бідність"
        },
        urban_population: {
            colorLow: "#f7f4f9",
            colorHigh: "#49006a",
            label: "Міське населення"
        },
        birth_rate: {
            colorLow: "#f7fcfd",
            colorHigh: "#014636",
            label: "Народжуваність"
        },
        median_age: {
            colorLow: "#f7f4e9",
            colorHigh: "#7f3b08",
            label: "Медіанний вік"
        },
        internet_users: {
            colorLow: "#e0f3f8",
            colorHigh: "#08589e",
            label: "Користувачі Інтернету (%)"
        },
        mobile_subscriptions: {
            colorLow: "#fee0d2",
            colorHigh: "#de2d26",
            label: "Мобільні підписки (на 100 осіб)"
        },
        poverty_gap: {
            colorLow: "#f7fcf5",
            colorHigh: "#00441b",
            label: "Розрив бідності (%)"
        },
        health_expenditure: {
            colorLow: "#f1eef6",
            colorHigh: "#810f7c",
            label: "Витрати на здоров'я (% ВВП)"
        },
        school_enrollment: {
            colorLow: "#e5f5e0",
            colorHigh: "#238b45",
            label: "Охоплення школою (%)"
        },
        homicide_rate: {
            colorLow: "#fee5d9",
            colorHigh: "#a50f15",
            label: "Рівень вбивств (на 100 тис.)"
        },
        energy_use: {
            colorLow: "#ffffcc",
            colorHigh: "#800026",
            label: "Використання енергії (кг нафтового еквіваленту на особу)"
        },
        urbanization_rate: {
            colorLow: "#f7fcfd",
            colorHigh: "#045a8d",
            label: "Рівень урбанізації (%)"
        }
    };

    // --- Карта ---
    const map = L.map('map', {
        center: [20, 0],
        zoom: 2,
        minZoom: 2,
        maxZoom: 6,
        maxBounds: [[-90, -180], [90, 180]],
        maxBoundsViscosity: 1.0
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    let legend = L.control({ position: 'bottomright' });
    legend.onAdd = function(map) {
        let div = L.DomUtil.create('div', 'info legend');
        div.style.background = 'white';
        div.style.padding = '10px';
        div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
        updateLegend(div);
        return div;
    };
    legend.addTo(map);

    function updateLegend(legendDiv) {
        let conf = legendConfig[currentIndicator];
        if (!conf) return;
        let range = computeIndicatorRange(currentCache, currentIndicator, currentYear);
        // --- Максимальне значення для легенди — половина від реального максимуму ---
        let legendMax = Math.round(range.max / 2);
        legendDiv.innerHTML = `
            <div style="text-align: center; margin-bottom: 5px; font-weight:bold;">${conf.label}</div>
            <div style="background: linear-gradient(to right, ${conf.colorLow}, ${conf.colorHigh}); width: 100%; height: 12px; margin: 5px 0;"></div>
            <div style="font-size: 14px; display: flex; justify-content: space-between;">
                <div>Мін: <strong>${range.min.toLocaleString('uk-UA')}</strong></div>
                <div>Макс: <strong>${legendMax.toLocaleString('uk-UA')}</strong></div>
            </div>
        `;
    }

    function computeIndicatorRange(cache, indicator, year) {
        let values = [];
        if (cache.worldbank) {
            Object.entries(cache.worldbank)
                .filter(([key]) => key.startsWith(`${indicator}_`) && key.endsWith(`_${year}`))
                .forEach(([_, val]) => { if (val !== null) values.push(val); });
        }
        if (values.length === 0) return { min: 0, max: 1 };
        return { min: 0, max: Math.max(...values) };
    }

    function populateCountryList(geojsonData) {
        const datalist = document.getElementById('countryList');
        let countries = new Set();
        geojsonData.features.forEach(feature => {
            let name = getCountryName(feature);
            if (name) {
                countries.add(name);
            }
        });
        datalist.innerHTML = "";
        countries.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            datalist.appendChild(option);
        });
    }

    // --- Динамічне оновлення повзунка років ---
    function updateYearSlider() {
        const indicator = indicatorSelect.value;
        // --- Фіксований повзунок років до 2023 ---
        yearSlider.min = 1980;
        yearSlider.max = 2023;
        if (parseInt(yearSlider.value) > 2023) {
            yearSlider.value = 2023;
            yearDisplay.textContent = 2023;
            currentYear = 2023;
        }
        let sliderLabels = document.getElementById('sliderLabels');
        if (sliderLabels) sliderLabels.remove();
    }

    function loadCache() {
        fetch('/data?t=' + new Date().getTime())
            .then(res => res.json())
            .then(data => {
                currentCache = data;
                updateYearSlider();
                updateBoundariesStyle();
                let legendDiv = document.querySelector('.legend');
                if (legendDiv) updateLegend(legendDiv);
                loadFinalGeoJSON();
            })
            .catch(err => console.error("Помилка завантаження даних:", err));
    }

    function showInfoForSelectedCountry(geojsonData) {
        const country = countryInput.value.trim();
        if (!country) return;
        let found = null;
        for (let feature of geojsonData.features) {
            let name = getCountryName(feature);
            let iso = getCountryISOFromFeature(feature);
            if (
                (name && name.toLowerCase() === country.toLowerCase()) ||
                (iso && iso.toLowerCase() === country.toUpperCase()) ||
                (countryMapping[iso] && countryMapping[iso].toLowerCase() === country.toLowerCase())
            ) {
                found = feature;
                break;
            }
        }
        if (found) displayCountryInfo(found);
    }

    function loadFinalGeoJSON() {
        // Додаємо indicator і year до запиту
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;
        fetch(`/geojson?indicator=${indicator}&year=${year}`)
            .then(response => response.json())
            .then(data => {
                if (finalLayer) {
                    map.removeLayer(finalLayer);
                }
                finalLayer = L.geoJSON(data, {
                    style: styleFeature,
                    onEachFeature: function(feature, layer) {
                        layer.on('click', function() {
                            displayCountryInfo(feature);
                        });
                    }
                }).addTo(map);
                showInfoForSelectedCountry(data); // Додаємо показ інфи одразу після завантаження geojson
                console.log("Фінальний шар GeoJSON додано на карту");
            })
            .catch(err => console.error("Помилка завантаження фінальних даних:", err));
    }

    // Функція, яка оновлює відведену для даних панель на сайті (без pop-up на карті)
    function displayCountryInfo(feature) {
        // --- Використовуємо ISO-код для пошуку даних ---
        let isoCode = getCountryISOFromFeature(feature);
        let country = isoCode ? countryMapping[isoCode] : feature.properties.country;
        let indicatorText = indicatorSelect.options[indicatorSelect.selectedIndex].text;
        let value;
        let year = feature.properties.year || currentYear;
        let cacheKey = `${currentIndicator}_${isoCode || country}_${year}`;
        const yearVal = parseInt(year);
        // --- універсальний пошук для всіх показників ---
        if (yearVal <= 2023) {
            if (currentCache.worldbank && currentCache.worldbank[cacheKey] !== undefined) {
                value = currentCache.worldbank[cacheKey];
            } else {
                value = feature.properties[currentIndicator] || feature.properties.population || feature.properties.unemployment_rate || "Немає даних";
            }
        }
        // --- Формуємо таблицю динаміки за 5 років ---
        let tableRows = "";
        let prevVal = null;
        for (let i = 5; i >= 1; i--) {
            let y = yearVal - i;
            if (y < 1980) continue;
            let key = `${currentIndicator}_${isoCode || country}_${y}`;
            let val = currentCache.worldbank && currentCache.worldbank[key] !== undefined ? currentCache.worldbank[key] : null;
            let diff = (val !== null && prevVal !== null && typeof val === "number" && typeof prevVal === "number") ? (val - prevVal) : null;
            let diffStr = diff !== null ? (diff > 0 ? "+" : "") + diff.toLocaleString('uk-UA') : "";
            tableRows += `<tr><td>${y}</td><td>${val !== null ? val.toLocaleString('uk-UA') : "—"}</td><td>${diffStr}</td></tr>`;
            prevVal = val;
        }
        // Додаємо обраний рік (без зміни)
        tableRows += `<tr style='font-weight:bold; background:#f0f0f0;'><td>${yearVal}</td><td>${typeof value === "number" ? value.toLocaleString('uk-UA') : value}</td><td></td></tr>`;
        let historyHtml = `
            <div style="margin-top:10px; border-left:2px solid #ccc; padding-left:10px;">
                <strong>Динаміка за 5 років:</strong>
                <table style="width:100%; font-size:13px; margin-top:5px; border-collapse:collapse;">
                    <thead><tr><th>Рік</th><th>Значення</th><th>Зміна</th></tr></thead>
                    <tbody>${tableRows}</tbody>
                </table>
            </div>
        `;
        infoPanel.innerHTML = `
            <div style="display:flex; flex-direction:row; gap:20px; align-items:flex-start;">
                <div>
                    <h3>Країна: ${country}</h3>
                    <p>${indicatorText}: ${typeof value === "number" ? value.toLocaleString('uk-UA') : value}</p>
                    <p>Рік: ${year}</p>
                </div>
                <div style="min-width:220px;">${historyHtml}</div>
            </div>
        `;
        countryInput.value = country;
    }

    fetch('/static/country_boundaries.geojson')
        .then(res => res.json())
        .then(data => {
            populateCountryList(data);
            boundariesLayer = L.geoJSON(data, {
                style: styleFeature,
                onEachFeature: function(feature, layer) {
                    let countryName = getCountryName(feature);
                    if (countryName) {
                        layer.on('click', function() {
                            countryInput.value = countryName;
                            triggerUpdate();
                        });
                    }
                }
            }).addTo(map);
        })
        .catch(err => console.error("Помилка завантаження кордонів:", err));

    function updateBoundariesStyle() {
        if (boundariesLayer) {
            boundariesLayer.setStyle(styleFeature);
        }
    }

    function styleFeature(feature) {
        const year = yearSlider.value;
        const yearVal = parseInt(year);
        let isoCode = getCountryISOFromFeature(feature);
        let countryName = isoCode ? isoCode : getWorldbankCountry(getCountryName(feature));
        let cacheKey = `${currentIndicator}_${countryName.toUpperCase()}_${year}`;
        let value = null;
        if (yearVal <= 2023) {
            if (currentCache.worldbank && currentCache.worldbank[cacheKey] !== undefined) {
                value = currentCache.worldbank[cacheKey];
            }
        }
        let style = {
            fillColor: '#ccc',
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.7
        };
        if (value !== null && value !== undefined) {
            let range = computeIndicatorRange(currentCache, currentIndicator, year);
            let conf = legendConfig[currentIndicator] || {colorLow: "#edf8e9", colorHigh: "#006d2c"};
            style.fillColor = interpolateColor(value, range.min, range.max, conf.colorLow, conf.colorHigh);
        }
        const selectedInput = getWorldbankCountry(countryInput.value);
        let selectedCompare = Array.isArray(selectedInput) ? selectedInput : [selectedInput];
        if (selectedCompare.some(val => val.toUpperCase() === countryName.toUpperCase())) {
            style.weight = 3;
            style.color = '#FFD700';
        }
        return style;
    }

    function interpolateColor(value, min, max, colorLow, colorHigh) {
        let ratio = (value - min) / (max - min);
        ratio = Math.max(0, Math.min(1, ratio));
        function hexToRgb(hex) {
            let bigint = parseInt(hex.slice(1), 16);
            return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
        }
        function rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        }
        let low = hexToRgb(colorLow);
        let high = hexToRgb(colorHigh);
        let r = Math.round(low.r + (high.r - low.r) * ratio);
        let g = Math.round(low.g + (high.g - low.g) * ratio);
        let b = Math.round(low.b + (high.b - low.b) * ratio);
        return rgbToHex(r, g, b);
    }

    function loadGeoJSON() {
        fetch('/data?t=' + new Date().getTime())
            .then(res => res.json())
            .then(data => {
                currentCache = data;
                updateBoundariesStyle();
                let legendDiv = document.querySelector('.legend');
                if (legendDiv) updateLegend(legendDiv);
                loadFinalGeoJSON();
            })
            .catch(err => {
                console.error("Помилка завантаження даних:", err);
                infoPanel.innerHTML = `<h3>Помилка завантаження даних</h3><p>${err}</p>`;
            });
    }

    function triggerUpdate() {
        const country = countryInput.value.trim();
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;
        // --- Додаємо перевірку: якщо не обрано показник або країну, не робимо fetch ---
        if (!indicator) {
            infoPanel.innerHTML = `<h3>Оберіть показник</h3><p>Спочатку виберіть показник зі списку.</p>`;
            return;
        }
        if (!country) {
            infoPanel.innerHTML = `<h3>Оберіть країну</h3><p>Спочатку введіть або виберіть країну зі списку.</p>`;
            return;
        }
        showLoadingMessage();
        fetch(`/update?indicator=${indicator}&country=${encodeURIComponent(country)}&year=${year}`)
            .then(res => res.json())
            .then(data => {
                console.log("Update response:", data);
                setTimeout(loadGeoJSON, 1500);
            })
            .catch(err => {
                console.error("Update error:", err);
                infoPanel.innerHTML = `<h3>Помилка оновлення</h3>`;
            });
    }

    function showLoadingMessage() {
        infoPanel.innerHTML = `
            <h3>Обробка даних...</h3>
            <p>Зачекайте, триває оновлення даних.</p>
        `;
    }

    // --- Завантаження PGF-звіту ---
    document.getElementById('downloadReportBtn').addEventListener('click', function() {
        const indicator = document.getElementById('indicatorSelect').value;
        const country = document.getElementById('countryInput').value;
        const year = document.getElementById('yearSlider').value;
        const heatmap = document.getElementById('heatmapOption').checked;
        const linechart = document.getElementById('linechartOption').checked;
        const statschart = document.getElementById('statschartOption').checked;

        if (!indicator || !country) {
            alert('Оберіть показник і країну для формування звіту!');
            return;
        }
        if (!heatmap && !linechart && !statschart) {
            alert('Оберіть хоча б одну опцію для звіту!');
            return;
        }

        fetch('/download_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                indicator,
                country,
                year,
                heatmap,
                linechart,
                statschart
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Помилка формування звіту');
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'report.pgf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(err => {
            alert('Не вдалося сформувати звіт: ' + err.message);
        });
    });

    // --- Події ---
    countryInput.addEventListener("blur", triggerUpdate); // Оновлення при втраті фокусу
    countryInput.addEventListener("keyup", e => { if (e.key === "Enter") triggerUpdate(); }); // Оновлення при Enter
    indicatorSelect.addEventListener("change", function() {
        currentIndicator = indicatorSelect.value;
        updateYearSlider();
        triggerUpdate();
    });
    yearSlider.addEventListener("input", function() {
        currentYear = yearSlider.value;
        yearDisplay.textContent = currentYear;
        triggerUpdate();
    });

    // --- Початкове завантаження ---
    infoPanel.innerHTML = `
        <h3>Інформаційна Панель</h3>
        <p>Введіть країну, виберіть показник та рік для перегляду даних.</p>
    `;
});
