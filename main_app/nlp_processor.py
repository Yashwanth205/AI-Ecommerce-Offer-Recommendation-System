import nltk
import os

# ✅ Download NLTK data on Render
nltk_data_dir = "/tmp/nltk_data"
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)
nltk.download("punkt", download_dir=nltk_data_dir, quiet=True)
nltk.download("punkt_tab", download_dir=nltk_data_dir, quiet=True)
nltk.download("stopwords", download_dir=nltk_data_dir, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words("english"))


def process_query(user_input):
    user_input = user_input.lower()
    words = word_tokenize(user_input)
    filtered_words = [w for w in words if w.isalnum() and w not in stop_words]
    cleaned_query = " ".join(filtered_words)
    return cleaned_query if cleaned_query else user_input