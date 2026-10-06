import re
 
import pandas as pd
 
# e.g. "09/09/25, 7:15 pm"  (also handles 24h time and 4-digit years)
TS = r"\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?:\s?[AaPp][Mm])?"
MSG_RE = re.compile(rf"^({TS}) - ([^:]{{1,60}}?): (.*)$")  # "<time> - Name: text"
SYS_RE = re.compile(rf"^{TS} - ")                          # any timestamped line
 
FORMATS = [
    "%d/%m/%y, %I:%M %p",
    "%d/%m/%Y, %I:%M %p",
    "%d/%m/%y, %H:%M",
    "%d/%m/%Y, %H:%M",
]
EDIT_TAG = "<This message was edited>"
 
 
def preprocess(raw: str) -> pd.DataFrame:
    # Newer exports use invisible characters (narrow no-break space, LTR marks)
    for ch in ("\u202f", "\u00a0"):
        raw = raw.replace(ch, " ")
    for ch in ("\u200e", "\u200f", "\ufeff"):
        raw = raw.replace(ch, "")
 
    rows, in_msg = [], False
    for line in raw.splitlines():
        m = MSG_RE.match(line)
        if m:
            rows.append(list(m.groups()))
            in_msg = True
        elif SYS_RE.match(line):
            # System line ("X joined", "Y created group"...): skip it, and make
            # sure it is NOT glued onto the previous message.
            in_msg = False
        elif in_msg:
            rows[-1][2] += " " + line  # continuation of a multi-line message
 
    if not rows:
        raise ValueError(
            "No messages found. Export the chat from WhatsApp as a .txt file and try again."
        )
 
    df = pd.DataFrame(rows, columns=["Stamp", "Name", "Message"])
 
    # Try each date format and keep the one that parses the most rows
    stamp = df["Stamp"].str.upper()
    parsed = [pd.to_datetime(stamp, format=f, errors="coerce") for f in FORMATS]
    df["DateTime"] = max(parsed, key=lambda s: s.notna().sum())
    df = df.dropna(subset=["DateTime"]).drop(columns="Stamp")
    if df.empty:
        raise ValueError("Couldn't read the dates in this file.")
 
    df["Name"] = df["Name"].str.strip()
    msg = df["Message"].str.strip()
    df["Edited"] = msg.str.contains(EDIT_TAG, regex=False)
    msg = msg.str.replace(EDIT_TAG, "", regex=False).str.strip()
    df["Message"] = msg
 
    # Message types
    df["IsMedia"] = msg.str.fullmatch(
        r"<Media omitted>|(?:image|video|audio|sticker|GIF|document) omitted"
    )
    df["IsDeleted"] = msg.isin(["This message was deleted", "You deleted this message"])
    df["IsPoll"] = msg.str.startswith("POLL:")
 
    # Date parts
    dt = df["DateTime"].dt
    df["OnlyDate"] = dt.normalize()
    df["Year"] = dt.year
    df["Month"] = dt.month
    df["MonthName"] = dt.month_name()
    df["Day"] = dt.day
    df["Hour"] = dt.hour
    df["Day Name"] = dt.day_name()
 
    return df.reset_index(drop=True)
 
