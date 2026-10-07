# WhatsApp Chat Analyzer

A web app that turns an exported WhatsApp chat into interactive statistics and charts. Upload a `.txt` export and explore who talks the most, when the chat is busiest, which words and emojis come up most often, and more.

**Live demo:** [whatsappchatanalyer.streamlit.app](https://whatsappchatanalyer-tgmiratdweqknhsatgzock.streamlit.app/)

## Features

- **Overview:** total messages, words, media and links, plus active days, average words per message and the busiest hour of the day.
- **Timelines:** monthly and daily message counts.
- **Activity patterns:** busiest weekday, busiest month, and a day-by-hour heatmap.
- **User comparison:** top 10 chatters and a table with messages, words, media, links, share of the chat and average words per message for every member.
- **Word analysis:** word cloud, most common words, and a word search that shows how often a word was used, when, and by whom.
- **Emoji analysis:** most used emojis with counts.
- **Filters:** analyze the whole group or a single person, narrow the results to a date range, and add your own words to ignore.

The stop word list supports Hinglish, so common filler words in mixed Hindi and English chats are filtered out of the word statistics.

## How to use

1. In WhatsApp, open the chat and choose **More > Export chat > Without media**.
2. Open the app and upload the exported `.txt` file from the sidebar.
3. Pick a user, a date range, and browse the tabs.

The uploaded file is read in memory for your session and is not saved by the app.

## Run locally

```bash
git clone https://github.com/mohit78145/whatsapp_chat_analyer.git
cd whatsapp_chat_analyer
pip install -r requirements.txt
streamlit run app.py
```

Requires Python 3.9 or newer.

## Project structure

```
.
├── app.py              Streamlit interface and charts
├── helper.py           Analysis functions (stats, timelines, words, emojis)
├── preprocessor.py     Parses the exported chat into a DataFrame
├── stop_hinglish.txt   Stop words for English and Hinglish
└── requirements.txt    Python dependencies
```

## Tech stack

- Python
- Streamlit
- Pandas
- Matplotlib and Seaborn
- WordCloud
- emoji

## Notes

- The parser expects the standard WhatsApp export format, for example `09/09/25, 7:15 pm - Name: message`. Both 12-hour and 24-hour times are supported.
- System messages such as members joining or leaving are ignored, and edited, deleted and poll messages are excluded from word statistics.

## Author

Mohit ([@mohit78145](https://github.com/mohit78145))
