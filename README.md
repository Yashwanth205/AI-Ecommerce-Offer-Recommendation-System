# AI E-Commerce Offer Recommendation System

## Overview
This project is an AI-powered system that compares product offers from multiple e-commerce websites and recommends the best deal.

The system fetches offers from different stores, ranks them using a machine learning model, and explains the recommendation using an AI model.

---

## Features
- Multi-store product search
- AI-based deal ranking
- Real-time price monitoring agent
- Email alerts for price drops
- Watchlist for tracking products
- AI explanation for recommended deals
- User authentication (login/register)

---

## Technologies Used
- Python
- Flask
- SQLite
- Scikit-learn
- Ollama (LLM)
- HTML / CSS / Bootstrap
- JavaScript

---

## Project Structure


AI_Ecommerce_Offer_Recommendation_System
│
├── main_app
│ ├── app.py
│ ├── fetcher.py
│ ├── scorer.py
│ ├── price_agent.py
│ └── templates
│
├── ecommerce_sites
│ ├── ecommerce_site_1
│ └── ecommerce_site_2
│
├── database
│ ├── deal_model.pkl
│ └── training_data.csv
│
└── requirements.txt


---

# Project Screenshots

## All Products with Ranking
![Ranking](images/All%20products%20with%20ranking.png)

## Best Recommended Deal
![Best Deal](images/Best%20recommended%20deal%20with%20explanation.png)

## Watchlist
![Watchlist](images/watchlist.png)

## Price Drop Email Alert
![Email Alert](images/Price%20drop%20Alert%20message%20to%20mail.png)

## After Price Drop
![Price Drop](images/After%20price%20Drop.png)

---

## Installation

Clone the repository


git clone https://github.com/Yashwanth205/AI-Ecommerce-Offer-Recommendation-System.git


Install dependencies


pip install -r requirements.txt


Run the application


python app.py


---

## Author
Yashwanth
