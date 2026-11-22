import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bike Sharing Demand", page_icon="🚲", layout="wide")

SEASONS = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
WEATHER = {1: "Clear / Few clouds", 2: "Mist / Cloudy", 3: "Light rain / Snow", 4: "Heavy rain / Snow"}
DAYS = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@st.cache_data
def load_data(file=None):
    df = pd.read_csv(file or "data/hour.csv", parse_dates=["dteday"])
    df["Year"] = df.yr.map({0: 2011, 1: 2012})
    df["Season"] = df.season.map(SEASONS)
    df["Weather"] = df.weathersit.map(WEATHER)
    df["Day type"] = df.workingday.map({0: "Non-working day", 1: "Working day"})
    df["Weekday"] = df.weekday.map(DAYS)
    df["Month"] = df.mnth.map(lambda m: MONTHS[m - 1])
    df["Temp (°C)"] = df.temp * 47 - 8
    df["Humidity (%)"] = df.hum * 100
    df["Wind (raw)"] = df.windspeed * 67
    return df


st.title("🚲 Bike Sharing Demand — Washington D.C. (2011–2012)")
st.caption("Hourly rentals from the UCI Bike Sharing dataset. Use the sidebar filters; every chart and number updates.")

try:
    df = load_data()
except FileNotFoundError:
    up = st.file_uploader("data/hour.csv not found. Upload hour.csv:", type="csv")
    if up is None:
        st.stop()
    df = load_data(up)

# ---------------- Filters ----------------
st.sidebar.header("Filters")
years = st.sidebar.multiselect("Year", [2011, 2012], default=[2011, 2012])
seasons = st.sidebar.multiselect("Season", list(SEASONS.values()), default=list(SEASONS.values()))
day_types = st.sidebar.multiselect("Day type", ["Working day", "Non-working day"],
                                   default=["Working day", "Non-working day"])
weathers = st.sidebar.multiselect("Weather", list(WEATHER.values()), default=list(WEATHER.values()))
hours = st.sidebar.slider("Hour of day", 0, 23, (0, 23))
tmin, tmax = float(df["Temp (°C)"].min()), float(df["Temp (°C)"].max())
temps = st.sidebar.slider("Temperature (°C)", round(tmin), round(tmax) + 1, (round(tmin), round(tmax) + 1))

f = df[
    df.Year.isin(years)
    & df.Season.isin(seasons)
    & df["Day type"].isin(day_types)
    & df.Weather.isin(weathers)
    & df.hr.between(*hours)
    & df["Temp (°C)"].between(*temps)
]
if f.empty:
    st.warning("No data for these filters. Widen the selection.")
    st.stop()

# ---------------- KPIs ----------------
daily = f.groupby("dteday").cnt.sum()
by_hr = f.groupby("hr").cnt.mean()
c = st.columns(5)
c[0].metric("Total rentals", f"{f.cnt.sum():,}")
c[1].metric("Avg per hour", f"{f.cnt.mean():.0f}")
c[2].metric("Avg per day", f"{daily.mean():,.0f}")
c[3].metric("Peak hour", f"{by_hr.idxmax()}:00", f"{by_hr.max():.0f} avg rentals")
c[4].metric("Registered share", f"{f.registered.sum() / f.cnt.sum():.0%}")

st.divider()

# ---------------- Charts ----------------
tab1, tab2, tab3, tab4 = st.tabs(["⏰ When", "📅 Season & trend", "🌦️ Weather", "👥 Who"])

with tab1:
    st.subheader("Q1. At what hours is demand highest?")
    g = f.groupby(["hr", "Day type"]).cnt.mean().reset_index()
    st.plotly_chart(px.line(g, x="hr", y="cnt", color="Day type", markers=True,
                            labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}), use_container_width=True)
    st.subheader("Hour × weekday heatmap")
    h = f.pivot_table(index="Weekday", columns="hr", values="cnt", aggfunc="mean").reindex(list(DAYS.values()))
    st.plotly_chart(px.imshow(h, aspect="auto", color_continuous_scale="YlOrRd",
                              labels={"x": "Hour", "color": "Avg rentals"}), use_container_width=True)

with tab2:
    st.subheader("Q2. How do seasons and growth affect demand?")
    a, b = st.columns(2)
    m = f.groupby(["mnth", "Year"]).cnt.mean().reset_index()
    a.plotly_chart(px.line(m, x="mnth", y="cnt", color=m.Year.astype(str), markers=True,
                           labels={"mnth": "Month", "cnt": "Avg rentals per hour", "color": "Year"},
                           title="Average rentals by month"), use_container_width=True)
    s = f.groupby("Season").cnt.mean().reindex(list(SEASONS.values())).reset_index()
    b.plotly_chart(px.bar(s, x="Season", y="cnt", labels={"cnt": "Avg rentals per hour"},
                          title="Average rentals by season"), use_container_width=True)
    d = daily.reset_index()
    d["7-day average"] = d.cnt.rolling(7).mean()
    st.plotly_chart(px.line(d, x="dteday", y=["cnt", "7-day average"],
                            labels={"dteday": "Date", "value": "Daily rentals", "variable": ""},
                            title="Daily total rentals"), use_container_width=True)

with tab3:
    st.subheader("Q3. How much does weather matter?")
    a, b = st.columns(2)
    w = f.groupby("Weather").cnt.mean().reset_index()
    a.plotly_chart(px.bar(w, x="Weather", y="cnt", labels={"cnt": "Avg rentals per hour"},
                          title="By weather condition"), use_container_width=True)
    t = f.groupby(f["Temp (°C)"].round()).cnt.mean().reset_index()
    b.plotly_chart(px.line(t, x="Temp (°C)", y="cnt", markers=True,
                           labels={"cnt": "Avg rentals per hour"}, title="By temperature"),
                   use_container_width=True)
    a, b = st.columns(2)
    hb = f.groupby(pd.cut(f["Humidity (%)"], range(0, 101, 10), include_lowest=True), observed=True).cnt.mean()
    a.plotly_chart(px.bar(x=hb.index.astype(str), y=hb.values,
                          labels={"x": "Humidity (%)", "y": "Avg rentals per hour"}, title="By humidity"),
                   use_container_width=True)
    wb = f.groupby(pd.cut(f["Wind (raw)"], [-1, 0, 10, 20, 30, 70]), observed=True).cnt.mean()
    b.plotly_chart(px.bar(x=wb.index.astype(str), y=wb.values,
                          labels={"x": "Wind speed", "y": "Avg rentals per hour"}, title="By wind speed"),
                   use_container_width=True)

with tab4:
    st.subheader("Q4. Casual vs registered riders")
    r = f.groupby("hr")[["casual", "registered"]].mean().reset_index().melt("hr", var_name="User type", value_name="Avg rentals")
    st.plotly_chart(px.line(r, x="hr", y="Avg rentals", color="User type", markers=True,
                            labels={"hr": "Hour of day"}), use_container_width=True)
    split = f.groupby("Day type")[["casual", "registered"]].sum().reset_index().melt("Day type", var_name="User type", value_name="Rentals")
    st.plotly_chart(px.bar(split, x="Day type", y="Rentals", color="User type", barmode="group"),
                    use_container_width=True)

st.divider()

# ---------------- Conclusions ----------------
st.header("📌 Conclusions")
full = df
fh = full.groupby(["hr", "Day type"]).cnt.mean()
y = full.groupby("Year").cnt.sum()
growth = y[2012] / y[2011] - 1
w_means = full.groupby("weathersit").cnt.mean()
st.markdown(f"""
1. **Demand is commuter-driven.** On working days there are two sharp peaks, at **8:00** and **17:00–18:00**
   (about {fh[(8, 'Working day')]:.0f} and {fh[(17, 'Working day')]:.0f} rentals per hour on average).
   On non-working days there is a single broad midday hump from about 11:00 to 16:00.
2. **Registered users create the peaks.** Registered riders follow the commute pattern;
   casual riders are a smaller, flatter afternoon group that matters more on weekends.
3. **Demand is seasonal.** Summer is the busiest season and winter the quietest, with winter roughly half of summer.
   Rentals rise with temperature up to the high 20s °C and fall off in extreme heat.
4. **The service grew strongly.** Total rentals rose **{growth:.0%}** from 2011 to 2012, so growth is a separate effect from seasonality.
5. **Bad weather cuts demand.** Average hourly rentals fall from {w_means[1]:.0f} in clear weather to {w_means[3]:.0f}
   in light rain or snow. High humidity and strong wind also reduce rentals.
6. **Day of the week matters little in total.** Weekday averages are similar; what changes is the *shape* of the day.

**Recommendations:** rebalance and service bikes before 8:00 and 16:00 on working days,
schedule maintenance in the overnight trough (0:00–5:00), and run promotions for casual riders on warm weekend afternoons.
""")
st.caption("Source: UCI Machine Learning Repository, Bike Sharing Dataset (Fanaee-T & Gama).")
