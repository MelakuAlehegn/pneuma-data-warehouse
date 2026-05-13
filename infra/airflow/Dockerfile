ARG AIRFLOW_VERSION=3.2.1
ARG PYTHON_VERSION=3.11
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
