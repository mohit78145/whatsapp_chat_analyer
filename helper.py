import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
 
import emoji
import pandas as pd
from wordcloud import WordCloud
 
URL_RE = re.compile(r"https?://\S+|www\.\S+")
WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")
 
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]
 
# Small built-in list so the app still works if stop_hinglish.txt is missing
BUILTIN_STOP = set(
    "the and for you are was this that with have not but but your will from".split()
)
# WhatsApp boilerplate that is not real conversation
SYSTEM_WORDS = {
    "message", "deleted", "edited", "omitted", "media", "pm", "am",
    "pinned", "joined", "null", "poll", "option", "options", "votes", "vote",
}
 
 
@lru_cache(maxsize=1)
def load_stop_words():
    path = Path(__file__).with_name("stop_hinglish.txt")  # next to this file
    words = set(BUILTIN_STOP)
    if path.exists():
        words |= set(path.read_text(encoding="utf-8").lower().split())
    return frozenset(words)
 
 
def filter_user(df, user):
    return df if user == "Overall" else df[df["Name"] == user]
 
 
#  stats
def fetch_stats(df):
    text = df[~df["IsMedia"] & ~df["IsDeleted"]]
    words = int(text["Message"].str.split().str.len().sum())
    hour = int(df["Hour"].value_counts().idxmax())
    return {
        "messages": len(df),
        "words": words,
        "media": int(df["IsMedia"].sum()),
        "links": int(df["Message"].str.count(URL_RE.pattern).sum()),
        "active_days": int(df["OnlyDate"].nunique()),
        "avg_words": round(words / max(len(text), 1), 1),
        "busiest_hour": pd.Timestamp(2000, 1, 1, hour).strftime("%I %p").lstrip("0"),
    }
 
 
def user_summary(df):
    d = df.assign(
        Words=df["Message"].str.split().str.len().where(~df["IsMedia"], 0),
        Links=df["Message"].str.count(URL_RE.pattern),
    )
    out = d.groupby("Name").agg(
        Messages=("Message", "size"),
        Words=("Words", "sum"),
        Media=("IsMedia", "sum"),
        Links=("Links", "sum"),
    )
    out["Share %"] = (out["Messages"] / out["Messages"].sum() * 100).round(2)
    out["Avg words/msg"] = (
        out["Words"] / (out["Messages"] - out["Media"]).clip(lower=1)
    ).round(1)
    return out.sort_values("Messages", ascending=False).reset_index()
 
 
#  timelines
def monthly_timeline(df):
    t = df.groupby(["Year", "Month"]).size().reset_index(name="Messages")  # sorted by date
    first = pd.to_datetime(pd.DataFrame({"year": t["Year"], "month": t["Month"], "day": 1}))
    t["Label"] = first.dt.strftime("%b %Y")
    return t
 
 
def daily_timeline(df):
    return df.groupby("OnlyDate").size().reset_index(name="Messages")
 
 
def week_activity_map(df):
    return df["Day Name"].value_counts().reindex(DAYS, fill_value=0)
 
 
def month_activity_map(df):
    return df["MonthName"].value_counts().reindex(MONTHS, fill_value=0)
 
 
def activity_heatmap(df):
    return df.pivot_table(
        index="Day Name", columns="Hour", values="Message", aggfunc="count", fill_value=0
    ).reindex(index=DAYS, columns=range(24), fill_value=0)
 
 
#  words
def get_words(df, extra_stop=()):
    stop = load_stop_words() | SYSTEM_WORDS | {w.lower() for w in extra_stop}
    text = df[~(df["IsMedia"] | df["IsDeleted"] | df["IsPoll"])]
    words = []
    for msg in text["Message"]:
        msg = URL_RE.sub(" ", msg.lower())
        words += [w for w in WORD_RE.findall(msg) if len(w) > 2 and w not in stop]
    return words
 
 
def most_common_words(df, n=20, extra_stop=()):
    counts = Counter(get_words(df, extra_stop)).most_common(n)
    return pd.DataFrame(counts, columns=["word", "count"])
 
 
def create_wordcloud(df, extra_stop=()):
    freq = Counter(get_words(df, extra_stop))
    if not freq:
        return None
    wc = WordCloud(
        width=900, height=450, background_color="white",
        min_font_size=10, max_words=150, collocations=False,
    )
    return wc.generate_from_frequencies(freq)
 
 
def word_search(df, word):
    """Messages containing `word` (whole word), with a hit count per message."""
    word = word.strip().lower()
    if not word:
        return None
    hits = df[~df["IsMedia"]].copy()
    hits["Hits"] = hits["Message"].str.lower().str.count(rf"\b{re.escape(word)}\b")
    return hits[hits["Hits"] > 0]
 
 
# emojis
def emoji_helper(df):
    emojis = []
    for message in df.loc[~df["IsMedia"], "Message"]:
        # emoji_list handles multi-character emojis (flags, skin tones, families)
        emojis.extend(e["emoji"] for e in emoji.emoji_list(message))
    return pd.DataFrame(Counter(emojis).most_common(), columns=["emoji", "count"])
 
