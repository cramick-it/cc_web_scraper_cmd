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


# Crawl EyeWiki
poetry run scrape crawl --site eyewiki

# Crawl Medical News Today
poetry run scrape crawl --site medicalnewstoday

# Sa vidljivim browserom (debug mode)
poetry run scrape crawl --site eyewiki --visible --limit 5


poetry run scrape scrape_eyewiki --visible --limit 5
poetry run scrape scrape_medicalnewstoday --visible --limit 5

# Normalno pokretanje
poetry run scrape crawl --site medicalnewstoday

```

## MongoDB

```javascript
db.pages.createIndex({url: 1}, {unique: true})
db.headings.createIndex({url: 1})
db.headings.createIndex({'heading.checksum': 1})
```


## Utils

Pauzirajte izvršavanje da vidite šta se dešava:
```
page.pause()  # Dodajte ovo u kod gde želite da pauzirate
```


Snimite screenshot za probleme:
```
page.screenshot(path=f"screenshot_{i}.png")
```


Proverite selektore u browser konzoli:
```
// U browser konzoli
document.querySelectorAll('.category-page__member-link').length
```