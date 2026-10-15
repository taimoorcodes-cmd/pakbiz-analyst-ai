# PakBiz AI Analyst

An AI-powered data analyst for Pakistani small businesses. Upload a CSV file, ask questions in English or Urdu, and get instant answers with charts.

## What Does It Do

- Upload any CSV file
- Ask questions like "What is the total revenue?"
- The AI converts your question into SQL
- It runs the query and shows you the answer
- It creates a chart automatically
- You can download the result as PDF

## How To Use It

1. Upload a CSV file from the sidebar
2. Click Clean and Load
3. Ask any question in English or Urdu
4. See the answer, chart, and SQL used

## Example Questions

- What is the total revenue?
- Top 5 selling customers
- Which city has most orders?
- Sabse zyada sale kaunsi category ki hai?

## Built With

- LangGraph for AI workflow
- OpenRouter for free AI models
- Streamlit for the web app
- SQLite for database
- Pandas for data handling
- Plotly for charts

## How To Run It Locally

1. Clone the repo
2. Install packages with pip install -r requirements.txt
3. Create a .env file with your OpenRouter API key
4. Run: streamlit run app.py

## Features

- Works in English and Roman Urdu
- Auto cleans the data (removes empty rows, fixes nulls)
- Shows KPI cards for single answers
- Creates bar charts for comparisons
- Handles gibberish questions politely
- SQL injection protection
- Download reports as PDF or CSV

## Author

Taimoor Ghalib

GitHub: https://github.com/taimoorcodes-cmd

## Note

This is my learning project. I built it while learning AI and web development. Feel free to try it and give feedback.
