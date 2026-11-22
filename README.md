# 🚲 Bike Sharing Demand Explorer

Interactive Streamlit app analysing **17,379 hourly bike rentals** in Washington D.C. (2011–2012, UCI Bike Sharing Dataset).

**Live app:** https://bike-sharing-app-karim-mohamed-almamlouk.streamlit.app/

## What the app shows
| Tab | Question answered |
|---|---|
| ⏰ When | At which hours is demand highest, on working vs non-working days? (line chart + hour × weekday heatmap) |
| 📅 Season & trend | How do months, seasons and year-over-year growth affect rentals? |
| 🌦️ Weather | How do weather condition, temperature, humidity and wind change demand? |
| 👥 Who | How do casual and registered riders differ? |

**Filters (sidebar):** year, season, day type, weather, hour range, temperature range.
**KPIs:** total rentals, average per hour, average per day, peak hour, registered share.
**Conclusions:** plain-language findings and recommendations at the bottom of the app.

## Key findings
- Working days have commute peaks at 8:00 and 17:00–18:00; non-working days have one midday hump.
- Registered users drive the peaks; casual users ride mostly in the afternoon.
- Summer is busiest, winter quietest; demand rises with temperature and drops in rain/snow.
- Rentals grew strongly from 2011 to 2012.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Requires `data/hour.csv` (download from the UCI link in `data/README.txt`). If the file is missing, the app lets you upload it.

## Files
- `app.py` – the Streamlit app
- `requirements.txt` – dependencies
- `data/hour.csv` – dataset (add this yourself)

## Data source
Fanaee-T, H. & Gama, J. (2013). Bike Sharing Dataset, UCI Machine Learning Repository.
