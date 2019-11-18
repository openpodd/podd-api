FROM python:2.7.14

RUN apt-get update && apt-get install -y \
		gcc \
		gettext \
		postgresql-client libpq-dev \
		sqlite3 \
		libgeos-dev libproj-dev gdal-bin libjpeg-dev \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/src/app /usr/src/lib
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN cp -R /usr/src/app/src/* /usr/src/lib/

VOLUME /usr/src/app
EXPOSE 8000

ENV PYTHONPATH=/usr/src/lib/podd-form-generator:/usr/src/lib/pyth:/usr/src/lib/larva
ENV DJANGO_SETTINGS_MODULE podd.settings.docker
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
