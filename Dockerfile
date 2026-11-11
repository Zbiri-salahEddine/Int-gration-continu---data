FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ pipeline/
COPY sql/ sql/

RUN useradd --system pipeline
USER pipeline

CMD ["python", "-m", "pipeline.planificateur"]
