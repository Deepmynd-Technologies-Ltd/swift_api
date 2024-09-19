FROM python:3.12.5-slim
RUN pip install --upgrade pip
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY /build.sh .
ENTRYPOINT [ "sh", "build.sh" ]