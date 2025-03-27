# CareCommons srcapper

## Install dependencies and setup

```
# Initialize Poetry
poetry install

# Install Playwright browsers
poetry run playwright install

# Start MongoDB with Docker Compose
docker compose up -d

# Copy .env.example to .env
cp .env.example .env
```


### Install the shell plugin (if you really want poetry shell back)

```
poetry self add poetry-plugin-shell
```

After installing the plugin, you can use:
```
poetry shell
```


## Running the application

```
# Activate Poetry shell
poetry shell

poetry env use python3.13
poetry env activate

# Run the CLI tool
scrape --help
scrape scrape --url "https://example.com"
```


