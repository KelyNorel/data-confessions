# Data Confessions
### Does Rain Reduce Crime? A Multi-Agent Causal Analysis System

A multi-agent AI system that investigates whether rainfall causally reduces crime in Chicago,
using LangGraph for agent orchestration and Claude as the reasoning engine.

---

## Data Sources

### Crime Data
- **Source:** City of Chicago Data Portal
- **URL:** https://data.cityofchicago.org/resource/ijzp-q8t2.csv
- **Method:** Downloaded via API (see `download_data.py`)
- **Period:** 2018–2023
- **Size:** 50,000 records
- **Fields:** date, primary_type, arrest, domestic, latitude, longitude

### Weather Data
- **Source:** Open-Meteo Historical Weather API
- **URL:** https://open-meteo.com/en/docs/historical-weather-api
- **Method:** Downloaded manually via web interface
- **Parameters:**
  - Location: Chicago, IL (latitude: 41.85, longitude: -87.65)
  - Period: 2018-01-01 to 2023-12-31
  - Timezone: America/Chicago
  - Daily variables: Precipitation Sum, Rain Sum, Max Temperature, Min Temperature
- **File saved as:** `data/raw/weather.csv`

---

*More sections coming soon: Architecture, Agents, Setup, Results*