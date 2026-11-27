import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bike Sharing Demand", page_icon="🚲", layout="wide")

SEASONS = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
WEATHER = {1: "Clear / Few clouds", 2: "Mist / Cloudy", 3: "Light rain / Snow", 4: "Heavy rain / Snow"}
DAYS = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def show(fig):
    """Display a plotly chart full-width (works on old and new Streamlit)."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def load_data(file=None):
    df = pd.read_csv(file or "data/hour.csv", parse_dates=["dteday"])
    df["Year"] = df.yr.map({0: 2011, 1: 2012})
    df["Season"] = df.season.map(SEASONS)
    df["Weather"] = df.weathersit.map(WEATHER)
    df["Day type"] = df.workingday.map({0: "Non-working day", 1: "Working day"})
    df["Day category"] = "Weekend"
    df.loc[df.workingday == 1, "Day category"] = "Working day"
    df.loc[df.holiday == 1, "Day category"] = "Holiday"
    df["Weekday"] = df.weekday.map(DAYS)
    df["Month"] = df.mnth.map(lambda m: MONTHS[m - 1])
    df["Temp (°C)"] = df.temp * 47 - 8
    df["Feels-like (°C)"] = df.atemp * 66 - 16
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
tmin, tmax = round(float(df["Temp (°C)"].min())), round(float(df["Temp (°C)"].max())) + 1
temps = st.sidebar.slider("Temperature (°C)", tmin, tmax, (tmin, tmax))

# base = all filters except year (used for the year-over-year question)
base = df[
    df.Season.isin(seasons)
    & df["Day type"].isin(day_types)
    & df.Weather.isin(weathers)
    & df.hr.between(*hours)
    & df["Temp (°C)"].between(*temps)
]
f = base[base.Year.isin(years)]
if f.empty:
    st.warning("No data for these filters. Widen the selection.")
    st.stop()

# ---------------- KPIs ----------------
daily = f.groupby("dteday").cnt.sum()
by_hr = f.groupby("hr").cnt.mean()
c = st.columns(6)
c[0].metric("Total rentals", f"{f.cnt.sum():,}")
c[1].metric("Avg per hour", f"{f.cnt.mean():.0f}")
c[2].metric("Avg per day", f"{daily.mean():,.0f}")
c[3].metric("Peak hour", f"{by_hr.idxmax()}:00", f"{by_hr.max():.0f} avg rentals")
c[4].metric("Registered share", f"{f.registered.sum() / f.cnt.sum():.0%}")
c[5].metric("Busiest day", f"{daily.max():,}", str(daily.idxmax().date()))

st.divider()

# ---------------- Charts ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["⏰ When", "📅 Season & trend", "🌦️ Weather", "👥 Who", "🔬 Deep dive"])

# ===== TAB 1: WHEN =====
with tab1:
    st.subheader("Q1. At what hours is demand highest?")
    g = f.groupby(["hr", "Day type"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Day type", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))

    st.subheader("Q2. Which weekday and hour combinations are busiest?")
    h = f.pivot_table(index="Weekday", columns="hr", values="cnt", aggfunc="mean").reindex(list(DAYS.values()))
    show(px.imshow(h, aspect="auto", color_continuous_scale="YlOrRd",
                   labels={"x": "Hour", "color": "Avg rentals"}))

    st.subheader("Q3. Do public holidays behave like weekends or like working days?")
    g = f.groupby(["hr", "Day category"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Day category", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))

# ===== TAB 2: SEASON & TREND =====
with tab2:
    st.subheader("Q4. How do seasons and growth affect demand?")
    a, b = st.columns(2)
    m = f.groupby(["mnth", "Year"]).cnt.mean().reset_index()
    with a:
        show(px.line(m, x="mnth", y="cnt", color=m.Year.astype(str), markers=True,
                     labels={"mnth": "Month", "cnt": "Avg rentals per hour", "color": "Year"},
                     title="Average rentals by month"))
    s = f.groupby("Season").cnt.mean().reindex(list(SEASONS.values())).reset_index()
    with b:
        show(px.bar(s, x="Season", y="cnt", labels={"cnt": "Avg rentals per hour"},
                    title="Average rentals by season"))
    d = daily.reset_index()
    d["7-day average"] = d.cnt.rolling(7).mean()
    show(px.line(d, x="dteday", y=["cnt", "7-day average"],
                 labels={"dteday": "Date", "value": "Daily rentals", "variable": ""},
                 title="Daily total rentals"))

    st.subheader("Q5. Was growth from 2011 to 2012 the same in every month?")
    mm = base.pivot_table(index="mnth", columns="Year", values="cnt", aggfunc="sum")
    if {2011, 2012}.issubset(mm.columns):
        gr = ((mm[2012] / mm[2011] - 1) * 100).reset_index(name="Growth %")
        gr["Month"] = gr.mnth.map(lambda x: MONTHS[x - 1])
        show(px.bar(gr, x="Month", y="Growth %", title="Year-over-year growth in total rentals (2012 vs 2011)"))
        st.caption("Uses all sidebar filters except Year.")
    else:
        st.info("Not enough data for both years with the current filters.")

    st.subheader("Q6. Which were the busiest and the quietest days?")
    day_info = (f.groupby("dteday")
                  .agg(Rentals=("cnt", "sum"), Weekday=("Weekday", "first"), Season=("Season", "first"),
                       **{"Avg temp (°C)": ("Temp (°C)", "mean")})
                  .reset_index().rename(columns={"dteday": "Date"}))
    day_info["Date"] = day_info.Date.dt.date
    day_info["Avg temp (°C)"] = day_info["Avg temp (°C)"].round(1)
    a, b = st.columns(2)
    a.markdown("**Top 10 busiest days**")
    a.dataframe(day_info.nlargest(10, "Rentals"), hide_index=True)
    b.markdown("**Top 10 quietest days**")
    b.dataframe(day_info.nsmallest(10, "Rentals"), hide_index=True)
    st.caption("Days are totals within the current filters.")

# ===== TAB 3: WEATHER =====
with tab3:
    st.subheader("Q7. How much does weather matter?")
    a, b = st.columns(2)
    w = f.groupby("Weather").cnt.mean().reset_index()
    with a:
        show(px.bar(w, x="Weather", y="cnt", labels={"cnt": "Avg rentals per hour"}, title="By weather condition"))
    t = f.groupby(f["Temp (°C)"].round()).cnt.mean().reset_index()
    with b:
        show(px.line(t, x="Temp (°C)", y="cnt", markers=True,
                     labels={"cnt": "Avg rentals per hour"}, title="By temperature"))
    a, b = st.columns(2)
    hb = f.groupby(pd.cut(f["Humidity (%)"], range(0, 101, 10), include_lowest=True), observed=True).cnt.mean()
    with a:
        show(px.bar(x=hb.index.astype(str), y=hb.values,
                    labels={"x": "Humidity (%)", "y": "Avg rentals per hour"}, title="By humidity"))
    wb = f.groupby(pd.cut(f["Wind (raw)"], [-1, 0, 10, 20, 30, 70]), observed=True).cnt.mean()
    with b:
        show(px.bar(x=wb.index.astype(str), y=wb.values,
                    labels={"x": "Wind speed", "y": "Avg rentals per hour"}, title="By wind speed"))

    st.subheader("Q8. Does bad weather erase the commute peaks or just shrink them?")
    g = f.groupby(["hr", "Weather"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Weather", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))

    st.subheader("Q9. Which weather variable is most strongly related to demand?")
    wcols = ["Temp (°C)", "Feels-like (°C)", "Humidity (%)", "Wind (raw)"]
    cr = f[wcols + ["cnt"]].corr()["cnt"].drop("cnt").reset_index()
    cr.columns = ["Variable", "Correlation with rentals"]
    show(px.bar(cr, x="Variable", y="Correlation with rentals", range_y=[-1, 1]))
    st.caption("Pearson correlation with hourly rentals. Temperature and feels-like temperature are almost the same signal.")

# ===== TAB 4: WHO =====
with tab4:
    st.subheader("Q10. How do casual and registered riders differ through the day?")
    r = f.groupby("hr")[["casual", "registered"]].mean().reset_index().melt("hr", var_name="User type", value_name="Avg rentals")
    show(px.line(r, x="hr", y="Avg rentals", color="User type", markers=True, labels={"hr": "Hour of day"}))
    split = f.groupby("Day type")[["casual", "registered"]].sum().reset_index().melt("Day type", var_name="User type", value_name="Rentals")
    show(px.bar(split, x="Day type", y="Rentals", color="User type", barmode="group"))

    st.subheader("Q11. When do casual riders make up the biggest share?")
    a, b = st.columns(2)
    cs = f.groupby("Season")[["casual", "cnt"]].sum()
    cs = (cs.casual / cs.cnt * 100).reindex(list(SEASONS.values())).reset_index(name="Casual share %")
    with a:
        show(px.bar(cs, x="Season", y="Casual share %", title="Casual share by season"))
    ch = f.groupby("hr")[["casual", "cnt"]].sum()
    ch = (ch.casual / ch.cnt * 100).reset_index(name="Casual share %")
    with b:
        show(px.line(ch, x="hr", y="Casual share %", markers=True, title="Casual share by hour"))

# ===== TAB 5: DEEP DIVE =====
with tab5:
    st.subheader("Q12. Which month and hour combinations are busiest?")
    mh = f.pivot_table(index="Month", columns="hr", values="cnt", aggfunc="mean").reindex(MONTHS)
    show(px.imshow(mh, aspect="auto", color_continuous_scale="YlOrRd",
                   labels={"x": "Hour", "color": "Avg rentals"}))

    st.subheader("Q13. How variable is hourly demand, and where are the outliers?")
    log_y = st.checkbox("Log scale on histogram", value=False)
    a, b = st.columns(2)
    with a:
        show(px.histogram(f, x="cnt", nbins=60, log_y=log_y,
                          labels={"cnt": "Rentals in one hour"}, title="Distribution of hourly rentals"))
    with b:
        show(px.box(f, x="hr", y="cnt", labels={"hr": "Hour", "cnt": "Rentals"}, title="Spread by hour"))
    st.caption(f"Skewness of hourly rentals: {f.cnt.skew():.2f}. A positive value means a long tail of very busy hours.")

st.divider()

# ---------------- Conclusions (computed on the full dataset) ----------------
st.header("📌 Conclusions")
fh = df.groupby(["hr", "Day type"]).cnt.mean()
y = df.groupby("Year").cnt.sum()
growth = y[2012] / y[2011] - 1
w_means = df.groupby("weathersit").cnt.mean()
dc = df.groupby("Day category").cnt.mean()
cas = df.groupby("Day type")[["casual", "cnt"]].sum()
cas_share = cas.casual / cas.cnt
corr = df[["Temp (°C)", "Feels-like (°C)", "Humidity (%)", "Wind (raw)", "cnt"]].corr()["cnt"].drop("cnt")
mmf = df.pivot_table(index="mnth", columns="Year", values="cnt", aggfunc="sum")
mg = (mmf[2012] / mmf[2011] - 1) * 100
dday = df.groupby("dteday").cnt.sum()
corr_txt = ", ".join(f"{k.split(' (')[0].lower()} {v:+.2f}" for k, v in corr.items())

st.markdown(f"""
1. **Demand is commuter-driven.** On working days there are two sharp peaks, at **8:00** and **17:00–18:00**
   (about {fh[(8, 'Working day')]:.0f} and {fh[(17, 'Working day')]:.0f} rentals per hour on average).
   On non-working days there is a single broad midday hump from about 11:00 to 16:00.
2. **Holidays follow the weekend pattern.** Average hourly rentals are {dc.get('Holiday', float('nan')):.0f} on holidays,
   {dc.get('Weekend', float('nan')):.0f} on weekends and {dc.get('Working day', float('nan')):.0f} on regular working days.
3. **Registered users create the peaks.** Registered riders follow the commute pattern. Casual riders are a smaller, flatter afternoon group:
   they are {cas_share['Non-working day']:.0%} of rentals on non-working days versus {cas_share['Working day']:.0%} on working days.
4. **Demand is seasonal.** Summer is the busiest season and winter the quietest, with winter roughly half of summer.
   Rentals rise with temperature up to the high 20s °C and fall off in extreme heat.
5. **The service grew strongly.** Total rentals rose **{growth:.0%}** from 2011 to 2012. Month by month the growth ranged
   from {mg.min():.0f}% to {mg.max():.0f}%, so growth is a separate effect from seasonality.
6. **Bad weather cuts demand.** Average hourly rentals fall from {w_means[1]:.0f} in clear weather to {w_means[3]:.0f}
   in light rain or snow. Of the four weather variables, **{corr.abs().idxmax()}** is most strongly related to demand
   (correlation {corr[corr.abs().idxmax()]:+.2f}). All four: {corr_txt}.
7. **Day of the week matters little in total.** Weekday averages are similar; what changes is the *shape* of the day.
8. **Extremes.** The busiest day had {dday.max():,} rentals ({dday.idxmax().date()}) and the quietest only {dday.min():,} ({dday.idxmin().date()}).
   Hourly demand is right-skewed: most hours are modest and a minority of commute hours are very busy.

**Recommendations:** rebalance and service bikes before 8:00 and 16:00 on working days,
schedule maintenance in the overnight trough (0:00–5:00), run promotions for casual riders on warm weekend afternoons,
and plan reduced fleet deployment for rainy or snowy days.
""")
st.caption("Source: UCI Machine Learning Repository, Bike Sharing Dataset (Fanaee-T & Gama).")
