# 🚲 Bike Sharing Demand Explorer

Interactive Streamlit app analysing **17,379 hourly bike rentals** in Washington D.C. (2011–2012, UCI Bike Sharing Dataset).

**Live app:** https://YOUR-APP-NAME.streamlit.app  *(replace after deploying)*

## What the app shows
Sixteen questions in six tabs. **Every question has a chart and a written ✅ answer** (answers are computed on the full dataset).

| Tab | Questions |
|---|---|
| ⏰ When | Q1 Which hours are busiest? Q2 Which weekday × hour combinations are busiest, and does the weekday matter? Q3 Do holidays behave like weekends or working days? |
| 📅 Season & trend | Q4 How do seasons and months affect demand? Q5 Was 2011→2012 growth the same in every month? Q6 Busiest and quietest days |
| 🌦️ Weather | Q7 How much does weather matter? Q8 Does bad weather erase the commute peaks? Q9 Which weather variable matters most? |
| 👥 Who | Q10 Casual vs registered riders through the day. Q11 When is the casual share highest? |
| 🔬 Deep dive | Q12 Busiest month × hour combinations. Q13 Variability and outliers |
| 🧹 Data & features | Q14 Is the data clean? Q15 Target distribution and log transform. Q16 Correlation matrix and redundant variables |

**Filters (sidebar):** year, season, day type, weather, hour range, temperature range.
**KPIs:** total rentals, average per hour, average per day, peak hour, registered share, busiest day.
**Conclusions:** plain-language findings and recommendations at the bottom of the app.

## Key findings
- Working days have commute peaks at 8:00 and 17:00–18:00; non-working days have one midday hump.
- Registered users drive the peaks; casual users ride mostly in the afternoon.
- Summer is busiest, winter quietest; demand rises with temperature and drops in rain/snow.
- Rentals grew strongly from 2011 to 2012; holidays look like weekends; temperature is the weather variable most tied to demand.

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
