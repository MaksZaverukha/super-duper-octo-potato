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
        "CIV": "Ivory CoastCZE",
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

    // --- Оновлена функція для API Ninjas ---
    function getApiNinjasCountry(input) {
        input = input.trim();
        // Якщо це Україна — повертаємо масив з двох варіантів
        if (
            input.toLowerCase() === "ukraine" ||
            input.toLowerCase() === "україна" ||
            input.toUpperCase() === "UKR"
        ) {
            return ["UKR", "Ukraine"];
        }
        // Якщо ввели вже код — повертаємо як є
        if (input.length === 3 && input === input.toUpperCase() && countryMapping[input]) {
            return input;
        }
        // Якщо ввели повну назву — повертаємо код
        for (let iso in countryMapping) {
            if (countryMapping[iso].toLowerCase() === input.toLowerCase()) {
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
        legendDiv.innerHTML = `
            <div style="text-align: center; margin-bottom: 5px; font-weight:bold;">${conf.label}</div>
            <div style="background: linear-gradient(to right, ${conf.colorLow}, ${conf.colorHigh}); width: 100%; height: 12px; margin: 5px 0;"></div>
            <div style="font-size: 14px; display: flex; justify-content: space-between;">
                <div>Мін: <strong>${range.min.toLocaleString('uk-UA')}</strong></div>
                <div>Макс: <strong>${range.max.toLocaleString('uk-UA')}</strong></div>
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
        if (cache.api_ninjas) {
            Object.entries(cache.api_ninjas)
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

    function loadCache() {
        fetch('/data?t=' + new Date().getTime())
            .then(res => res.json())
            .then(data => {
                currentCache = data;
                updateBoundariesStyle();
                updateInfoPanel();
                let legendDiv = document.querySelector('.legend');
                if (legendDiv) updateLegend(legendDiv);
                loadFinalGeoJSON();
            })
            .catch(err => console.error("Помилка завантаження даних:", err));
    }

    function loadFinalGeoJSON() {
        fetch('/geojson')
            .then(res => res.json())
            .then(data => {
                if (finalLayer) {
                    map.removeLayer(finalLayer);
                }
                finalLayer = L.geoJSON(data, {
                    style: {
                        color: "#3388ff",
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.4
                    },
                    onEachFeature: function(feature, layer) {
                        layer.bindPopup(
                            `<strong>Країна: ${feature.properties.country}</strong><br>${indicatorSelect.options[indicatorSelect.selectedIndex].text}: ${feature.properties.population.toLocaleString('uk-UA')}<br>Рік: ${feature.properties.year}`
                        );
                    }
                }).addTo(map);
                console.log("Фінальний шар GeoJSON додано на карту");
            })
            .catch(err => console.error("Помилка завантаження фінальних даних:", err));
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

    // --- Оновлена функція для панелі інформації ---
    function updateInfoPanel() {
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;
        const yearVal = parseInt(year);
        let selectedInput = (yearVal <= 2023)
            ? getWorldbankCountry(countryInput.value)
            : getApiNinjasCountry(countryInput.value);
        let value = null;
        let key = "";
        let keysArr = [];
        let allKeys = [];
        let foundKey = null;

        if (yearVal <= 2023) {
            if (currentCache.worldbank) {
                key = `${indicator}_${selectedInput.toUpperCase()}_${year}`;
                value = currentCache.worldbank[key];
                allKeys = Object.keys(currentCache.worldbank);
                keysArr = allKeys.filter(k => k.endsWith(`_${year}`));
                foundKey = allKeys.find(k => k.toLowerCase().includes(selectedInput.toLowerCase()) && k.startsWith(`${indicator}_`) && k.endsWith(`_${year}`));
            }
        } else {
            if (currentCache.api_ninjas) {
                // --- ДЛЯ УКРАЇНИ ---
                if (Array.isArray(selectedInput)) {
                    for (let variant of selectedInput) {
                        key = `${indicator}_${variant}_${year}`;
                        value = currentCache.api_ninjas[key];
                        if (value !== undefined && value !== null) {
                            foundKey = key;
                            break;
                        }
                    }
                    allKeys = Object.keys(currentCache.api_ninjas);
                    keysArr = allKeys.filter(k => k.endsWith(`_${year}`));
                } else {
                    key = `${indicator}_${selectedInput}_${year}`;
                    value = currentCache.api_ninjas[key];
                    allKeys = Object.keys(currentCache.api_ninjas);
                    keysArr = allKeys.filter(k => k.endsWith(`_${year}`));
                    foundKey = allKeys.find(k => k.toLowerCase().includes(selectedInput.toLowerCase()) && k.startsWith(`${indicator}_`) && k.endsWith(`_${year}`));
                }
            }
        }
        const indicatorName = indicatorSelect.options[indicatorSelect.selectedIndex].text;
        if (value !== null && value !== undefined) {
            infoPanel.innerHTML = `
                <h3>Дані для ${Array.isArray(selectedInput) ? foundKey.split('_')[1] : selectedInput}</h3>
                <p>${indicatorName}: ${value.toLocaleString('uk-UA')}</p>
                <p>Рік: ${year}</p>
            `;
        } else {
            infoPanel.innerHTML = `
                <h3>Дані відсутні</h3>
                <p>Немає даних для ${Array.isArray(selectedInput) ? selectedInput.join(' / ') : selectedInput} за ${year} рік.</p>
                <details style="margin-top:8px;">
                  <summary>Доступні ключі для цього року</summary>
                  <div style="max-height:120px;overflow:auto;font-size:12px;color:#555;">
                    ${keysArr.map(k => `<div>${k} : ${yearVal <= 2023 ? currentCache.worldbank[k] : currentCache.api_ninjas[k]}</div>`).join("")}
                  </div>
                </details>
            `;
        }
    }

    function styleFeature(feature) {
        const year = yearSlider.value;
        const yearVal = parseInt(year);
        let countryName = (yearVal <= 2023) ? getWorldbankCountry(getCountryName(feature)) : getApiNinjasCountry(getCountryName(feature));
        let cacheKey;
        if (yearVal <= 2023) {
            cacheKey = `${currentIndicator}_${countryName.toUpperCase()}_${year}`;
        } else {
            if (Array.isArray(countryName)) {
                // Для України — шукаємо перший існуючий ключ
                for (let variant of countryName) {
                    let key = `${currentIndicator}_${variant}_${year}`;
                    if (currentCache.api_ninjas && currentCache.api_ninjas[key] !== undefined) {
                        cacheKey = key;
                        break;
                    }
                }
                if (!cacheKey) cacheKey = `${currentIndicator}_${countryName[0]}_${year}`;
            } else {
                cacheKey = `${currentIndicator}_${countryName}_${year}`;
            }
        }
        let value = null;
        if (yearVal <= 2023) {
            if (currentCache.worldbank && currentCache.worldbank[cacheKey] !== undefined) {
                value = currentCache.worldbank[cacheKey];
            }
        } else {
            if (currentCache.api_ninjas && currentCache.api_ninjas[cacheKey] !== undefined) {
                value = currentCache.api_ninjas[cacheKey];
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
        const selectedInput = (yearVal <= 2023) ? getWorldbankCountry(countryInput.value) : getApiNinjasCountry(countryInput.value);
        let selectedCompare = Array.isArray(selectedInput) ? selectedInput : [selectedInput];
        if (selectedCompare.some(val => (yearVal <= 2023 ? val.toUpperCase() : val) === (yearVal <= 2023 ? countryName.toUpperCase() : countryName))) {
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
                updateInfoPanel();
                let legendDiv = document.querySelector('.legend');
                if (legendDiv) updateLegend(legendDiv);
                loadFinalGeoJSON();
            })
            .catch(err => console.error("Помилка завантаження даних:", err));
    }

    function triggerUpdate() {
        const country = countryInput.value.trim();
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;
        if (parseInt(year) > 2023 && (!country || country.toUpperCase() === 'ALL')) {
            infoPanel.innerHTML = `
                <h3>Увага!</h3>
                <p>Для років після 2023 потрібно вибрати конкретну країну.</p>
            `;
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
    // --- Події ---
    countryInput.addEventListener("change", triggerUpdate);
    indicatorSelect.addEventListener("change", function() {
        currentIndicator = indicatorSelect.value;
        triggerUpdate();
    });
    yearSlider.addEventListener("input", function() {
        currentYear = yearSlider.value;
        yearDisplay.textContent = currentYear;
        triggerUpdate();
    });

    // --- Початкове завантаження ---
    loadGeoJSON();
});