import nltk

# ✅ Safe download (only if missing)
try:
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
except:
    nltk.download('stopwords')
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))

try:
    from nltk.tokenize import word_tokenize
    word_tokenize("test")
except:
    nltk.download('punkt')
    from nltk.tokenize import word_tokenize


def process_query(user_input):
    # 1. lowercase
    user_input = user_input.lower()

    # 2. tokenize
    words = word_tokenize(user_input)

    # 3. remove stopwords
    filtered_words = []
    for word in words:
        if word.isalnum() and word not in stop_words:
            filtered_words.append(word)

    # 4. join
    cleaned_query = " ".join(filtered_words)

    return cleaned_query