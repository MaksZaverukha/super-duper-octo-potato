document.addEventListener("DOMContentLoaded", function() {
    // Глобальні змінні
    let currentCache = {};
    let currentIndicator = document.getElementById('indicatorSelect').value;
    let currentYear = document.getElementById('yearSlider').value;
    let boundariesLayer;
    let finalLayer;
    let updateTimeout = null; // Змінна для таймауту

    // DOM-елементи
    const countryInput = document.getElementById('countryInput');
    const countryDatalist = document.getElementById('countryList');
    const indicatorSelect = document.getElementById('indicatorSelect');
    const yearSlider = document.getElementById('yearSlider');
    const yearDisplay = document.getElementById('yearDisplay');
    const infoPanel = document.getElementById('infoPanel');

    // Таблиця відповідностей
    const countryMapping = {
        "UKR": "Ukraine",
        "USA": "USA",
        "CHN": "China"
    };

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

    function getApiNinjasCountry(input) {
        return input.trim();
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

    // Конфігурація легенди
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

    // Функції для роботи з легендою та стилями залишаються без змін...

    // Оновлена функція triggerUpdate з підтримкою затримки
    function triggerUpdate(immediate = false) {
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

        // Очищаємо попередній таймаут
        if (updateTimeout) {
            clearTimeout(updateTimeout);
        }

        // Якщо immediate=true або це не подія повзунка, оновлюємо одразу
        if (immediate) {
            showLoadingMessage();
            performUpdate();
        } else {
            // Інакше чекаємо 500мс перед оновленням
            updateTimeout = setTimeout(() => {
                showLoadingMessage();
                performUpdate();
            }, 500);
        }
    }

    // Виділена функція для виконання оновлення
    function performUpdate() {
        const country = countryInput.value.trim();
        const indicator = indicatorSelect.value;
        const year = yearSlider.value;

        fetch(`/update?indicator=${indicator}&country=${encodeURIComponent(country)}&year=${year}`)
            .then(res => res.json())
            .then(data => {
                console.log("Відповідь оновлення:", data);
                setTimeout(loadGeoJSON, 1500);
            })
            .catch(err => {
                console.error("Помилка оновлення:", err);
                infoPanel.innerHTML = `<h3>Помилка оновлення</h3>`;
            });
    }

    // Оновлені обробники подій
    countryInput.addEventListener("change", () => triggerUpdate(true));
    indicatorSelect.addEventListener("change", () => {
        currentIndicator = indicatorSelect.value;
        triggerUpdate(true);
    });

    // Новий обробник для повзунка
    yearSlider.addEventListener("input", function() {
        currentYear = yearSlider.value;
        yearDisplay.textContent = currentYear;
        // Оновлюємо тільки відображення року без запиту до сервера
        updateInfoPanel();
    });

    // Додаємо новий обробник для події відпускання повзунка
    yearSlider.addEventListener("change", function() {
        triggerUpdate(true);
    });

    // Початкове завантаження
    loadGeoJSON();
});