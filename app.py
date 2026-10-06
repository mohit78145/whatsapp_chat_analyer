
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
 
import helper
import preprocessor
 
st.set_page_config(page_title="WhatsApp Chat Analyzer",layout="wide")
sns.set_theme(style="whitegrid")
 
 
@st.cache_data(show_spinner="Reading chat...")
def load(raw: str):
    return preprocessor.preprocess(raw)
 
 
def show(fig):
    st.pyplot(fig)
    plt.close(fig)
 
 
def barh(labels, values, color, figsize=(8, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh([str(l) for l in labels], list(values), color=color)
    ax.invert_yaxis()  # biggest on top
    show(fig)
 
 
# sidebar
st.sidebar.title(" WhatsApp Chat Analyzer")
file = st.sidebar.file_uploader("Upload exported chat (.txt)", type="txt")
 
if file is None:
    st.title("WhatsApp Chat Analyzer")
    st.info(
        "Export a chat from WhatsApp (⋮ → More → Export chat → Without media) "
        "and upload the .txt file in the sidebar."
    )
    st.stop()
 
try:
    df = load(file.getvalue().decode("utf-8-sig"))
except ValueError as err:
    st.error(str(err))
    st.stop()
 
user = st.sidebar.selectbox("Show analysis for", ["Overall"] + sorted(df["Name"].unique()))
 
lo, hi = df["OnlyDate"].min().date(), df["OnlyDate"].max().date()
rng = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
if len(rng) != 2:
    st.info("Pick an end date in the sidebar.")
    st.stop()
 
extra_stop = [
    w.strip()
    for w in st.sidebar.text_input("Extra words to ignore (comma-separated)").split(",")
    if w.strip()
]
 
df_range = df[(df["OnlyDate"] >= pd.Timestamp(rng[0])) & (df["OnlyDate"] <= pd.Timestamp(rng[1]))]
d = helper.filter_user(df_range, user)
if d.empty:
    st.warning("No messages for this user in the selected date range.")
    st.stop()
 
st.title(f"Chat analysis: {user}")
tab_over, tab_act, tab_users, tab_words, tab_emoji = st.tabs(
    [" Overview", " Activity", " Users", " Words", " Emojis"]
)
 
# overview
with tab_over:
    s = helper.fetch_stats(d)
    c = st.columns(4)
    c[0].metric("Total messages", f"{s['messages']:,}")
    c[1].metric("Total words", f"{s['words']:,}")
    c[2].metric("Media messages", f"{s['media']:,}")
    c[3].metric("Links shared", f"{s['links']:,}")
    c = st.columns(3)
    c[0].metric("Active days", s["active_days"])
    c[1].metric("Avg words / message", s["avg_words"])
    c[2].metric("Busiest hour", s["busiest_hour"])
 
    st.subheader("Monthly timeline")
    t = helper.monthly_timeline(d)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(t["Label"], t["Messages"], marker="o", color="green")
    ax.tick_params(axis="x", rotation=90)
    show(fig)
 
    st.subheader("Daily timeline")
    t = helper.daily_timeline(d)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(t["OnlyDate"], t["Messages"], color="#1f77b4")
    ax.tick_params(axis="x", rotation=90)
    show(fig)
 
# activity
with tab_act:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Most busy day")
        day = helper.week_activity_map(d)
        fig, ax = plt.subplots()
        ax.bar(day.index, day.values, color="purple")
        ax.tick_params(axis="x", rotation=45)
        show(fig)
    with col2:
        st.subheader("Most busy month")
        month = helper.month_activity_map(d)
        fig, ax = plt.subplots()
        ax.bar(month.index, month.values, color="orange")
        ax.tick_params(axis="x", rotation=45)
        show(fig)
 
    st.subheader("When is the chat most active? (day × hour)")
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(helper.activity_heatmap(d), cmap="YlGnBu", ax=ax)
    ax.set_xlabel("Hour of day (24h)")
    ax.set_ylabel("")
    show(fig)
 
# users
with tab_users:
    if user != "Overall":
        st.info("Select **Overall** in the sidebar to compare users.")
    else:
        summary = helper.user_summary(df_range)
        st.subheader("Top 10 chatters")
        top = summary.head(10)
        barh(top["Name"], top["Messages"], "crimson", figsize=(8, 4.5))
        st.subheader("All users")
        st.dataframe(summary, hide_index=True)
 
#  words
with tab_words:
    st.subheader("Word cloud")
    wc = helper.create_wordcloud(d, extra_stop)
    if wc is None:
        st.info("Not enough text to build a word cloud.")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        show(fig)
 
    st.subheader("Most common words")
    n = st.slider("How many words?", 10, 50, 20)
    common = helper.most_common_words(d, n, extra_stop)
    barh(common["word"], common["count"], "#1f77b4", figsize=(8, max(4, n * 0.3)))
 
    
 
# emojis
with tab_emoji:
    e = helper.emoji_helper(d)
    if e.empty:
        st.info("No emojis found.")
    else:
        c = st.columns(2)
        c[0].metric("Total emojis", int(e["count"].sum()))
        c[1].metric("Unique emojis", len(e))
        st.dataframe(
            e.head(20),
            hide_index=True,
            column_config={
                "count": st.column_config.ProgressColumn(
                    "count", format="%d", min_value=0, max_value=int(e["count"].max())
                )
            },
        )
 
