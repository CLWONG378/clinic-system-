FROM python:3.11-slim

WORKDIR /app

# Upgrade pip and install packages
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all root files (admin, pages, assets, backend) into /app
COPY . .

WORKDIR /app/backend

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
