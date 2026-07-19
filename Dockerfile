FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8000
WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health'))['ok']"
CMD ["lambda-spec-lab", "--host", "0.0.0.0"]
