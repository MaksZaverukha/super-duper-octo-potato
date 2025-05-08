# Базовий образ
FROM ubuntu:22.04

# Уникаємо питань при встановленні пакетів
ENV DEBIAN_FRONTEND=noninteractive

# Оновлення та встановлення базових утиліт
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        wget \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
        locales \
        git \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-xetex \
        texlive-pictures \
        texlive-science \
        gdal-bin \
        libgdal-dev \
        libspatialindex-dev \
        libqt5core5a \
        libqt5gui5 \
        libqt5widgets5 \
        xvfb \
        && rm -rf /var/lib/apt/lists/*

# Додаємо офіційний репозиторій QGIS і ключ
RUN curl -fsSL https://qgis.org/downloads/qgis-2024.gpg.key | gpg --dearmor -o /usr/share/keyrings/qgis-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/qgis-archive-keyring.gpg] https://qgis.org/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/qgis.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends qgis python3-qgis && \
    rm -rf /var/lib/apt/lists/*

# Встановлення Python-залежностей
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Копіюємо весь код
COPY . .

# Відкриваємо порт для Flask
EXPOSE 5000

# Запуск Flask (можна змінити на gunicorn для продакшну)
CMD ["python3", "app.py"]
