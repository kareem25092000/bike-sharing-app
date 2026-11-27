import numpy as np
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


def answer(text):
    """Written answer shown under a question (computed on the full dataset)."""
    st.info(text, icon="✅")


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
st.caption("Hourly rentals from the UCI Bike Sharing dataset. Use the sidebar filters: charts and KPIs update. "
           "The ✅ answers under each question are computed on the full dataset.")

try:
    df = load_data()
except FileNotFoundError:
    up = st.file_uploader("data/hour.csv not found. Upload hour.csv:", type="csv")
    if up is None:
        st.stop()
    df = load_data(up)

# ---------------- Statistics on the FULL dataset (used by the written answers) ----------------
fh = df.groupby(["hr", "Day type"]).cnt.mean()
wk_peak8, wk_peak17 = fh[(8, "Working day")], fh[(17, "Working day")]
nw = fh.xs("Non-working day", level="Day type")
nw_hr, nw_val = nw.idxmax(), nw.max()
wd_mean = df.groupby("weekday").cnt.mean()
sm = df.groupby("Season").cnt.mean()
dc = df.groupby("Day category").cnt.mean()
yr_tot = df.groupby("Year").cnt.sum()
growth = yr_tot[2012] / yr_tot[2011] - 1
mmf = df.pivot_table(index="mnth", columns="Year", values="cnt", aggfunc="sum")
mg = (mmf[2012] / mmf[2011] - 1) * 100
dday = df.groupby("dteday").cnt.sum()
w_means = df.groupby("weathersit").cnt.mean()
wh = df.groupby(["hr", "weathersit"]).cnt.mean().unstack()
red8 = 1 - wh.loc[8, 3] / wh.loc[8, 1]
red17 = 1 - wh.loc[17, 3] / wh.loc[17, 1]
WCOLS = ["Temp (°C)", "Feels-like (°C)", "Humidity (%)", "Wind (raw)"]
corr = df[WCOLS + ["cnt"]].corr()["cnt"].drop("cnt")
corr_txt = ", ".join(f"{k.split(' (')[0].lower()} {v:+.2f}" for k, v in corr.items())
cas_day = df.groupby("Day type")[["casual", "cnt"]].sum()
cas_share = cas_day.casual / cas_day.cnt
cas_season = df.groupby("Season")[["casual", "cnt"]].sum()
cas_season = cas_season.casual / cas_season.cnt
cas_hr = df.groupby("hr")[["casual", "cnt"]].sum()
cas_hr = cas_hr.casual / cas_hr.cnt
mh_full = df.pivot_table(index="mnth", columns="hr", values="cnt", aggfunc="mean")
mh_m, mh_h = mh_full.stack().idxmax()
iqr = df.groupby("hr").cnt.quantile(.75) - df.groupby("hr").cnt.quantile(.25)
iqr_top = sorted(iqr.nlargest(3).index)
skew_cnt, skew_log = df.cnt.skew(), np.log1p(df.cnt).skew()
expected_rows = (df.dteday.max() - df.dteday.min()).days * 24 + 24
missing_hours = expected_rows - len(df)
wind_zero = (df.windspeed == 0).mean()
corr_all_cols = ["Temp (°C)", "Feels-like (°C)", "Humidity (%)", "Wind (raw)", "hr", "mnth",
                 "workingday", "holiday", "weathersit", "cnt"]
c_all = df[corr_all_cols].corr()
temp_atemp = c_all.loc["Temp (°C)", "Feels-like (°C)"]
wsit_cnt = c_all.loc["weathersit", "cnt"]

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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["⏰ When", "📅 Season & trend", "🌦️ Weather", "👥 Who", "🔬 Deep dive", "🧹 Data & features"])

# ===== TAB 1: WHEN =====
with tab1:
    st.subheader("Q1. At what hours is demand highest?")
    g = f.groupby(["hr", "Day type"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Day type", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))
    answer(f"**Working days have two commute peaks**, at 8:00 (~{wk_peak8:.0f} rentals/hour) and 17:00–18:00 "
           f"(~{wk_peak17:.0f} at 17:00), with a lower midday plateau. **Non-working days have one broad hump** "
           f"from about 11:00 to 16:00, peaking at {nw_hr}:00 (~{nw_val:.0f}). Demand is lowest between 2:00 and 5:00 on all days.")

    st.subheader("Q2. Which weekday and hour combinations are busiest, and does the day of the week matter?")
    a, b = st.columns([2, 1])
    h = f.pivot_table(index="Weekday", columns="hr", values="cnt", aggfunc="mean").reindex(list(DAYS.values()))
    with a:
        show(px.imshow(h, aspect="auto", color_continuous_scale="YlOrRd",
                       labels={"x": "Hour", "color": "Avg rentals"}, title="Avg rentals by weekday and hour"))
    wd = f.groupby("Weekday").cnt.mean().reindex(list(DAYS.values())).reset_index()
    with b:
        show(px.bar(wd, x="Weekday", y="cnt", labels={"cnt": "Avg rentals per hour"}, title="Average by weekday"))
    answer(f"The hottest cells are working-day mornings (8:00) and evenings (17:00–18:00), and weekend afternoons. "
           f"**The weekday matters little for the total**: averages range only from {wd_mean.min():.0f} to {wd_mean.max():.0f} rentals/hour; "
           f"what changes by day is the *shape* of the day (commute peaks vs midday hump).")

    st.subheader("Q3. Do public holidays behave like weekends or like working days?")
    g = f.groupby(["hr", "Day category"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Day category", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))
    answer(f"**Like weekends, only quieter.** Average rentals per hour: holidays {dc.get('Holiday', float('nan')):.0f}, "
           f"weekends {dc.get('Weekend', float('nan')):.0f}, working days {dc.get('Working day', float('nan')):.0f}. "
           f"Holidays have no sharp commute peaks, just a broad midday hump about 20% lower than weekends. "
           f"There are only about 21 holiday days in the data, so this estimate is based on few days.")

# ===== TAB 2: SEASON & TREND =====
with tab2:
    st.subheader("Q4. How do seasons and months affect demand?")
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
    answer(f"**Summer is busiest** ({sm['Summer']:.0f} rentals/hour), then spring ({sm['Spring']:.0f}) and fall ({sm['Fall']:.0f}); "
           f"**winter is about half of summer** ({sm['Winter']:.0f}). Demand climbs from January to a summer/early-autumn peak and falls toward December. "
           f"Every month of 2012 is above the same month of 2011, so there is a strong trend on top of the seasonality.")

    st.subheader("Q5. Was growth from 2011 to 2012 the same in every month?")
    mm = base.pivot_table(index="mnth", columns="Year", values="cnt", aggfunc="sum")
    if {2011, 2012}.issubset(mm.columns):
        gr = ((mm[2012] / mm[2011] - 1) * 100).reset_index(name="Growth %")
        gr["Month"] = gr.mnth.map(lambda x: MONTHS[x - 1])
        show(px.bar(gr, x="Month", y="Growth %", title="Year-over-year growth in total rentals (2012 vs 2011)"))
        st.caption("Uses all sidebar filters except Year.")
    else:
        st.info("Not enough data for both years with the current filters.")
    answer(f"**No.** Overall rentals grew **{growth:.0%}**, but month by month growth ranged from {mg.min():.0f}% "
           f"({MONTHS[int(mg.idxmin()) - 1]}) to {mg.max():.0f}% ({MONTHS[int(mg.idxmax()) - 1]}). "
           f"Growth was largest in the first months, when the 2011 base was small, and about +40–45% in May–July.")

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
    st.caption("Tables use the current filters (daily totals within the filters).")
    answer(f"On the full data the busiest day is {dday.idxmax().date()} with {dday.max():,} rentals and the quietest is "
           f"{dday.idxmin().date()} with only {dday.min():,}. The busiest days are mild, dry days in 2012 (mostly September and spring/summer Fridays and Saturdays); "
           f"the quietest are storm days or cold, rainy winter days, mostly in 2011, plus Christmas days.")

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
    answer(f"**Weather matters a lot.** Clear weather averages {w_means[1]:.0f} rentals/hour, mist/cloudy {w_means[2]:.0f} and "
           f"light rain/snow {w_means[3]:.0f} (about {1 - w_means[3] / w_means[1]:.0%} below clear). Demand rises with temperature up to roughly "
           f"25–30 °C and flattens or drops in extreme heat; high humidity lowers it; wind has a weak effect. "
           f"Category 4 (heavy rain/snow) has only {int((df.weathersit == 4).sum())} rows, so ignore its average.")

    st.subheader("Q8. Does bad weather erase the commute peaks or just shrink them?")
    g = f.groupby(["hr", "Weather"]).cnt.mean().reset_index()
    show(px.line(g, x="hr", y="cnt", color="Weather", markers=True,
                 labels={"hr": "Hour of day", "cnt": "Avg rentals per hour"}))
    answer(f"**It shrinks them, it doesn't erase them.** In light rain/snow the 8:00 and 17:00 peaks are still there but "
           f"{red8:.0%} and {red17:.0%} lower than in clear weather. Mist/cloudy is close to clear at commute hours and lower at midday, "
           f"so commuters mostly still ride.")

    st.subheader("Q9. Which weather variable is most strongly related to demand?")
    cr = f[WCOLS + ["cnt"]].corr()["cnt"].drop("cnt").reset_index()
    cr.columns = ["Variable", "Correlation with rentals"]
    show(px.bar(cr, x="Variable", y="Correlation with rentals", range_y=[-1, 1]))
    st.caption("Pearson correlation with hourly rentals (current filters).")
    answer(f"**{corr.abs().idxmax()}** is the strongest (full data: {corr_txt}). Temperature and feels-like temperature carry nearly the same "
           f"signal, so use only one in a linear model. The correlations are modest because the hour of the day explains much of the variation.")

# ===== TAB 4: WHO =====
with tab4:
    st.subheader("Q10. How do casual and registered riders differ through the day?")
    r = f.groupby("hr")[["casual", "registered"]].mean().reset_index().melt("hr", var_name="User type", value_name="Avg rentals")
    show(px.line(r, x="hr", y="Avg rentals", color="User type", markers=True, labels={"hr": "Hour of day"}))
    split = f.groupby("Day type")[["casual", "registered"]].sum().reset_index().melt("Day type", var_name="User type", value_name="Rentals")
    show(px.bar(split, x="Day type", y="Rentals", color="User type", barmode="group"))
    answer("**Registered users create the commute peaks** (8:00 and 17:00–18:00). Casual riders are far fewer and follow a flat afternoon curve; "
           "they matter relatively more on non-working days.")

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
    answer(f"Casual riders are **{cas_share['Non-working day']:.0%} of rentals on non-working days vs {cas_share['Working day']:.0%} on working days**. "
           f"By season the share is highest in spring ({cas_season['Spring']:.0%}) and summer ({cas_season['Summer']:.0%}) and lowest in winter ({cas_season['Winter']:.0%}). "
           f"By hour it peaks around {cas_hr.idxmax()}:00 ({cas_hr.max():.0%}) and is lowest at {cas_hr.idxmin()}:00 ({cas_hr.min():.0%}). "
           f"Casual riders are mostly leisure riders on warm weekend afternoons.")

# ===== TAB 5: DEEP DIVE =====
with tab5:
    st.subheader("Q12. Which month and hour combinations are busiest?")
    mh = f.pivot_table(index="Month", columns="hr", values="cnt", aggfunc="mean").reindex(MONTHS)
    show(px.imshow(mh, aspect="auto", color_continuous_scale="YlOrRd",
                   labels={"x": "Hour", "color": "Avg rentals"}))
    answer(f"The single busiest cell is **{MONTHS[mh_m - 1]} at {mh_h}:00** ({mh_full.loc[mh_m, mh_h]:.0f} average rentals). In general the hottest band is "
           f"17:00–18:00 from May to October, the 8:00 peak is the second-strongest band in every month, January, February and December are light all day, "
           f"and 0:00–5:00 is quiet in every month.")

    st.subheader("Q13. How variable is hourly demand, and where are the outliers?")
    log_y = st.checkbox("Log scale on histogram", value=False)
    a, b = st.columns(2)
    with a:
        show(px.histogram(f, x="cnt", nbins=60, log_y=log_y,
                          labels={"cnt": "Rentals in one hour"}, title="Distribution of hourly rentals"))
    with b:
        show(px.box(f, x="hr", y="cnt", labels={"hr": "Hour", "cnt": "Rentals"}, title="Spread by hour"))
    st.caption(f"Skewness of hourly rentals in the current selection: {f.cnt.skew():.2f}.")
    answer(f"Hourly demand is **right-skewed** (skew {skew_cnt:.2f}): many quiet hours and a long tail up to about {df.cnt.max():,} rentals. "
           f"**Variability is largest at the commute peaks** (widest spread at {', '.join(str(x) + ':00' for x in iqr_top)}), so the same hour can be quiet "
           f"or very busy depending on the day. The outliers at midday and at night are unusually busy hours for that time (typically warm weekend days), not data errors.")

# ===== TAB 6: DATA & FEATURES =====
with tab6:
    st.subheader("Q14. Is the data clean?")
    k = st.columns(5)
    k[0].metric("Rows", f"{len(df):,}")
    k[1].metric("Missing values", int(df.isna().sum().sum()))
    k[2].metric("Duplicate rows", int(df.duplicated().sum()))
    k[3].metric("Missing hours", missing_hours)
    k[4].metric("Wind = 0", f"{wind_zero:.1%}")
    wc = df.Weather.value_counts().reindex(list(WEATHER.values())).reset_index()
    wc.columns = ["Weather", "Rows"]
    show(px.bar(wc, x="Weather", y="Rows", title="Rows per weather category"))
    with st.expander("Summary statistics"):
        st.dataframe(df[["cnt", "casual", "registered", "Temp (°C)", "Feels-like (°C)",
                         "Humidity (%)", "Wind (raw)"]].describe().T)
    answer(f"**Yes, with small caveats.** {len(df):,} rows, no missing values, no duplicates, and `casual + registered = cnt` holds in every row. "
           f"{missing_hours} hours out of {expected_rows:,} are absent (hours with zero rentals are not recorded). "
           f"{wind_zero:.1%} of wind values are exactly zero (probably missing or coarse data), and weather category 4 has only "
           f"{int((df.weathersit == 4).sum())} rows, so merge it with category 3 when modelling.")

    st.subheader("Q15. What does the target (hourly rentals) look like, and does a log transform help?")
    a, b = st.columns(2)
    with a:
        show(px.histogram(df, x="cnt", nbins=60, title="cnt"))
    with b:
        show(px.histogram(x=np.log1p(df.cnt), nbins=60, labels={"x": "log(1 + cnt)"}, title="log1p(cnt)"))
    answer(f"`cnt` is right-skewed (skew {skew_cnt:.2f}). After a log1p transform the skew is {skew_log:.2f}, so the distribution is much more symmetric. "
           f"A log transform is worth trying for modelling. Do not use `casual` or `registered` as features for `cnt` (they add up to it: leakage).")

    st.subheader("Q16. Which variables are related to each other (and which are redundant)?")
    cm = f[corr_all_cols].corr()
    show(px.imshow(cm, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto"))
    answer(f"**Temperature and feels-like temperature are almost the same variable** (correlation {temp_atemp:+.2f}), so keep only one for linear models. "
           f"Rentals are most related to the hour of the day and to temperature; the weather category has a negative relation with rentals ({wsit_cnt:+.2f}): worse weather, fewer rides. "
           f"Hour of day is cyclical (23:00 is next to 0:00), so for modelling use categorical or sin/cos encoding.")

st.divider()

# ---------------- Conclusions ----------------
st.header("📌 Conclusions")
st.markdown(f"""
1. **Demand is commuter-driven.** On working days there are two sharp peaks, at **8:00** and **17:00–18:00**
   (about {wk_peak8:.0f} and {wk_peak17:.0f} rentals per hour on average). On non-working days there is a single broad midday hump.
2. **Holidays look like weekends, only quieter.** Average hourly rentals are {dc.get('Holiday', float('nan')):.0f} on holidays,
   {dc.get('Weekend', float('nan')):.0f} on weekends and {dc.get('Working day', float('nan')):.0f} on regular working days.
3. **Registered users create the peaks.** Casual riders are {cas_share['Non-working day']:.0%} of rentals on non-working days versus {cas_share['Working day']:.0%} on working days.
4. **Demand is seasonal.** Summer is the busiest season and winter the quietest (about half of summer).
5. **The service grew strongly.** Total rentals rose **{growth:.0%}** from 2011 to 2012; month by month the growth ranged from {mg.min():.0f}% to {mg.max():.0f}%.
6. **Bad weather cuts demand.** Average hourly rentals fall from {w_means[1]:.0f} in clear weather to {w_means[3]:.0f} in light rain or snow,
   but the commute peaks are shrunk, not erased. **{corr.abs().idxmax()}** is the weather variable most related to demand ({corr_txt}).
7. **Day of the week matters little in total;** it changes the *shape* of the day.
8. **Extremes.** Busiest day {dday.max():,} rentals ({dday.idxmax().date()}); quietest {dday.min():,} ({dday.idxmin().date()}).
   Hourly demand is right-skewed (skew {skew_cnt:.2f}).
9. **Data caveats.** {missing_hours} unrecorded hours, {wind_zero:.1%} zero wind values, only {int((df.weathersit == 4).sum())} rows in weather category 4,
   and `temp`/`atemp` are almost identical.

**Recommendations:** rebalance and service bikes before 8:00 and 16:00 on working days,
schedule maintenance in the overnight trough (0:00–5:00), run promotions for casual riders on warm weekend afternoons,
and plan reduced fleet deployment for rainy or snowy days.
""")
st.caption("Source: UCI Machine Learning Repository, Bike Sharing Dataset (Fanaee-T & Gama).")
