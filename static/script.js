document.addEventListener("DOMContentLoaded", function() {
    // Глобальні змінні
    let currentCache = {};
    let currentIndicator = document.getElementById('indicatorSelect').value;
    let currentYear = document.getElementById('yearSlider').value;
    let boundariesLayer;
    let finalLayer; // Шар фінальних даних з /geojson

    // DOM-елементи
    const countryInput = document.getElementById('countryInput');
    const countryDatalist = document.getElementById('countryList');
    const indicatorSelect = document.getElementById('indicatorSelect');
    const yearSlider = document.getElementById('yearSlider');
    const yearDisplay = document.getElementById('yearDisplay');
    const infoPanel = document.getElementById('infoPanel');

    // Таблиця відповідностей: для World Bank використовуємо ISO, для API Ninjas – повну назву
    const countryMapping = {
        "UKR": "Ukraine",
        "USA": "USA",
        "CHN": "China"
        // Додайте інші відповідності за потребою.
    };

    // Якщо користувач вводить ISO (3 символи) – повертаємо його,
    // інакше – шукаємо в mapping (наприклад, "Ukraine" → "UKR")
    function getWorldbankCountry(input) {
        input = input.trim();
        if (input.length === 3 && input === input.toUpperCase() && countryMapping[input]) {
            return input;
        } else {
            for (let iso in countryMapping) {
                if (countryMapping[iso].toLowerCase() === input.toLowerCase()) {
                    return iso;
                }
            }
            return input;
        }
    }

    // Для API Ninjas повертаємо повну назву без змін
    function getApiNinjasCountry(input) {
        return input.trim();
    }

    // Допоміжна функція для читання назви країни з властивостей фічі
    function getCountryName(feature) {
        // Перевіряємо можливі поля, де може зберігатися назва
        const fields = ["ADMIN", "NAME", "country"];
        for (let field of fields) {
            if (feature.properties && feature.properties[field]) {
                return feature.properties[field].trim();
            }
        }
        return "";
    }

    // Налаштування легенди
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

    // Ініціалізація карти
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

    // Додавання легенди
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

    // Обчислення діапазону: мінімум 0, максимум – найбільше значення з усіх країн для даного показника
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

    // Функція для заповнення списку країн (datalist) із завантаженого шару кордонів
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

    // Завантаження шару меж країн із бекенду
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

    // Оновлення інформаційної панелі
    // Для World Bank (рік <= 2023) використовуємо ISO (через getWorldbankCountry),
    // для API Ninjas (рік > 2023) – повну назву.
    function updateInfoPanel() {
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;
        const yearVal = parseInt(year);
        const selectedInput = (yearVal <= 2023) ? getWorldbankCountry(countryInput.value) : getApiNinjasCountry(countryInput.value);
        let value = null;
        if (yearVal <= 2023) {
            if (currentCache.worldbank) {
                let key = `${indicator}_${selectedInput.toUpperCase()}_${year}`;
                value = currentCache.worldbank[key];
            }
        } else {
            if (currentCache.api_ninjas) {
                let key = `${indicator}_${selectedInput}_${year}`;
                value = currentCache.api_ninjas[key];
            }
        }
        const indicatorName = indicatorSelect.options[indicatorSelect.selectedIndex].text;
        if (value !== null && value !== undefined) {
            infoPanel.innerHTML = `
                <h3>Дані для ${selectedInput}</h3>
                <p>${indicatorName}: ${value.toLocaleString('uk-UA')}</p>
                <p>Рік: ${year}</p>
            `;
        } else {
            infoPanel.innerHTML = `
                <h3>Дані відсутні</h3>
                <p>Немає даних для ${selectedInput} за ${year} рік.</p>
            `;
        }
    }

    // Стилізація країн на карті. Формуємо ключ залежно від року:
    // для World Bank – ISO (через getWorldbankCountry), для API Ninjas – повну назву.
    function styleFeature(feature) {
        const year = yearSlider.value;
        const yearVal = parseInt(year);
        let countryName = (yearVal <= 2023) ? getWorldbankCountry(getCountryName(feature)) : getApiNinjasCountry(getCountryName(feature));
        let cacheKey = (yearVal <= 2023)
            ? `${currentIndicator}_${countryName.toUpperCase()}_${year}`
            : `${currentIndicator}_${countryName}_${year}`;
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
        // Виділення країни, введеної користувачем
        const selectedInput = (yearVal <= 2023) ? getWorldbankCountry(countryInput.value) : getApiNinjasCountry(countryInput.value);
        if ((yearVal <= 2023 && selectedInput.toUpperCase() === countryName.toUpperCase()) ||
            (yearVal > 2023 && selectedInput === countryName)) {
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

    // Прив'язка подій
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

    // Початкове завантаження даних
    loadGeoJSON();
});
