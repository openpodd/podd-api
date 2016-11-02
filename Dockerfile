FROM python:2.7

RUN apt-get update && apt-get install -y \
		gcc \
		gettext \
		mysql-client libmysqlclient-dev \
		postgresql-client libpq-dev \
		sqlite3 \
		libgeos-dev libproj-dev gdal-bin libjpeg-dev \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /usr/src/app
EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE podd.settings.docker
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
