FROM python:3.12.5-slim
RUN apt-get update && apt-get install -y build-essential

RUN pip install --upgrade pip
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY /build.sh .
ENTRYPOINT [ "sh", "build.sh" ]