# Project image name
IMAGE=data_ingestion_test_runner

# Build Docker image from Dockerfile
build:
	docker build --no-cache -t $(IMAGE) .

# Run unit tests inside Docker
test:
	docker run --rm \
	  -v "$$(pwd)":/app \
	  -w /app \
	  --env-file .env \
	  $(IMAGE) \
	  pytest tests/

# Delete image
clean:
	docker rmi -f $(IMAGE)

# Copy env and spin up Airflow + Streamlit
up-all:
	@echo "➡️  Copying env if not exists..."
	cp -n .env.example .env || echo ".env already exists"

	@echo "Building and starting Airflow + Streamlit..."
	docker-compose up --build

# Convenience alias: build + test
all: build test
