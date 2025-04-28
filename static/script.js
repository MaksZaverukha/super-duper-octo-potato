document.addEventListener("DOMContentLoaded", function() {
    // Глобальні змінні
    let currentCache = {};
    let currentIndicator = document.getElementById('indicatorSelect').value;
    let currentYear = document.getElementById('yearSlider').value;

    // Елементи форми
    const countryInput = document.getElementById('countryInput');
    const countryDatalist = document.getElementById('countryList');
    const indicatorSelect = document.getElementById('indicatorSelect');
    const yearSlider = document.getElementById('yearSlider');
    const yearDisplay = document.getElementById('yearDisplay');
    const infoPanel = document.getElementById('infoPanel');

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

    // Завантаження даних
    function loadGeoJSON() {
        fetch('/data?t=' + new Date().getTime())
            .then(res => res.json())
            .then(data => {
                currentCache = data;
                updateBoundariesStyle();
                updateInfoPanel();
            })
            .catch(err => console.error("Error loading data:", err));
    }

    // Завантаження кордонів
    let boundariesLayer = null;
    fetch('/static/country_boundaries.geojson')
        .then(res => res.json())
        .then(data => {
            boundariesLayer = L.geoJSON(data, {
                style: styleFeature,
                onEachFeature: function(feature, layer) {
                    let iso = feature.properties.iso_a3 || feature.properties.ISO_A3;
                    if (iso) {
                        layer.on('click', function() {
                            countryInput.value = iso;
                            triggerUpdate();
                        });
                    }
                }
            }).addTo(map);
        })
        .catch(err => console.error("Error loading boundaries:", err));

    function updateInfoPanel() {
        const indicator = indicatorSelect.value;
        const country = countryInput.value.trim().toUpperCase();
        const year = yearSlider.value;
        const cacheKey = `${indicator}_${country}_${year}`;

        let value = null;
        if (currentCache.api_ninjas && currentCache.api_ninjas[cacheKey] !== undefined) {
            value = currentCache.api_ninjas[cacheKey];
        } else if (currentCache.worldbank && currentCache.worldbank[cacheKey] !== undefined) {
            value = currentCache.worldbank[cacheKey];
        }

        const indicatorName = indicatorSelect.options[indicatorSelect.selectedIndex].text;

        if (value !== null && value !== undefined) {
            infoPanel.innerHTML = `
                <h3>Дані для ${country}</h3>
                <p>${indicatorName}: ${value}</p>
                <p>Рік: ${year}</p>
            `;
        } else {
            infoPanel.innerHTML = `
                <h3>Дані відсутні</h3>
                <p>Немає даних для ${country} за ${year} рік.</p>
            `;
        }
    }

    function computeIndicatorRange(cache, indicator, year) {
        let values = [];

        if (cache.worldbank) {
            Object.entries(cache.worldbank)
                .filter(([key]) => key.startsWith(`${indicator}_`) && key.endsWith(`_${year}`))
                .forEach(([_, val]) => val !== null && values.push(val));
        }

        if (cache.api_ninjas) {
            Object.entries(cache.api_ninjas)
                .filter(([key]) => key.startsWith(`${indicator}_`) && key.endsWith(`_${year}`))
                .forEach(([_, val]) => val !== null && values.push(val));
        }

        return values.length ? {
            min: Math.min(...values),
            max: Math.max(...values)
        } : { min: 0, max: 1 };
    }

    function interpolateColor(value, min, max, colorLow, colorHigh) {
        const ratio = Math.max(0, Math.min(1, (value - min) / (max - min)));

        function hexToRgb(hex) {
            const bigint = parseInt(hex.slice(1), 16);
            return {
                r: (bigint >> 16) & 255,
                g: (bigint >> 8) & 255,
                b: bigint & 255
            };
        }

        function rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        }

        const low = hexToRgb(colorLow);
        const high = hexToRgb(colorHigh);

        return rgbToHex(
            Math.round(low.r + (high.r - low.r) * ratio),
            Math.round(low.g + (high.g - low.g) * ratio),
            Math.round(low.b + (high.b - low.b) * ratio)
        );
    }

    function styleFeature(feature) {
        const iso = (feature.properties.iso_a3 || feature.properties.ISO_A3 || '').toUpperCase();
        const cacheKey = `${currentIndicator}_${iso}_${currentYear}`;

        let value = null;
        if (currentCache.api_ninjas && currentCache.api_ninjas[cacheKey] !== undefined) {
            value = currentCache.api_ninjas[cacheKey];
        } else if (currentCache.worldbank && currentCache.worldbank[cacheKey] !== undefined) {
            value = currentCache.worldbank[cacheKey];
        }

        if (value === null || value === undefined) {
            return {
                fillColor: '#ccc',
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.7
            };
        }

        const range = computeIndicatorRange(currentCache, currentIndicator, currentYear);
        const fillColor = currentIndicator === "population"
            ? interpolateColor(value, range.min, range.max, "#fff7ec", "#7f0000")
            : interpolateColor(value, range.min, range.max, "#edf8e9", "#006d2c");

        return {
            fillColor: fillColor,
            weight: 1,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.7
        };
    }

    function updateBoundariesStyle() {
        if (boundariesLayer) {
            boundariesLayer.setStyle(styleFeature);
        }
    }

    function showLoadingMessage() {
        infoPanel.innerHTML = `
            <h3>Обробка даних...</h3>
            <p>Зачекайте, триває збір та обробка даних.</p>
        `;
    }

    function triggerUpdate() {
        const country = countryInput.value.trim();
        if (!country) return;

        showLoadingMessage();
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;

        fetch(`/update?indicator=${indicator}&country=${country}&year=${year}`)
            .then(res => res.json())
            .then(() => {
                setTimeout(loadGeoJSON, 1000);
            })
            .catch(error => console.error("Error updating data:", error));
    }

    let updateTimeout = null;
    function scheduleUpdate() {
        if (updateTimeout) clearTimeout(updateTimeout);
        updateTimeout = setTimeout(triggerUpdate, 1000);
    }

    // Завантаження списку країн
    fetch('/static/countries.json')
        .then(res => res.json())
        .then(countries => {
            countryDatalist.innerHTML = countries
                .map(country => `<option value="${country.iso}">${country.name}</option>`)
                .join('');
        })
        .catch(error => console.error("Error loading countries:", error));

    // Обробники подій
    yearSlider.addEventListener('input', function() {
    yearDisplay.textContent = this.value;
    currentYear = this.value;
    scheduleUpdate(); // Додаємо виклик оновлення при зміні року
});
    // Оновлена функція triggerUpdate
function triggerUpdate() {
    const country = countryInput.value.trim();
    const indicator = indicatorSelect.value;
    const year = yearSlider.value;

      // Перевіряємо чи є країна і чи змінився рік
    if (!country) {
        updateBoundariesStyle();
        updateInfoPanel();
        return;
    }
     showLoadingMessage();
    fetch(`/update?indicator=${indicator}&country=${country}&year=${year}&t=${new Date().getTime()}`)
        .then(res => res.json())
        .then(() => {
            setTimeout(loadGeoJSON, 1000);
        })
        .catch(error => {
            console.error("Помилка оновлення даних:", error);
            updateBoundariesStyle();
            updateInfoPanel();
        });
}

// Оновлена функція scheduleUpdate з меншою затримкою
function scheduleUpdate() {
    if (updateTimeout) clearTimeout(updateTimeout);
    updateTimeout = setTimeout(triggerUpdate, 500); // Зменшуємо затримку до 500мс
}

    countryInput.addEventListener('change', function() {
        scheduleUpdate();
    });

    indicatorSelect.addEventListener('change', function() {
        currentIndicator = this.value;
        updateBoundariesStyle();
        scheduleUpdate();
    });

    // Початкове завантаження
    loadGeoJSON();
});