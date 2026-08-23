FROM python:3.11-slim

WORKDIR /app

# Dependencies install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Project code copy karein
COPY . .

# Render dynamically PORT assign karta hai
EXPOSE 10000

CMD ["python", "main.py"]
