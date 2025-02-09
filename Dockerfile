FROM python:3.12-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (for caching optimization)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application files
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Apply database migrations
RUN python manage.py makemigrations
RUN python manage.py migrate

# Create superuser if the variable is set
RUN if [ "$CREATE_SUPERUSER" = "true" ]; then \
        echo "Creating superuser"; \
        python manage.py createsuperuser --no-input; \
    fi

# Set entry point for container execution
COPY build.sh .
ENTRYPOINT [ "sh", "build.sh" ]
