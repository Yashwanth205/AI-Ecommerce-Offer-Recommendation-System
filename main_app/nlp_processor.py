import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# load English stopwords
stop_words = set(stopwords.words('english'))

def process_query(user_input):
    # 1. make lowercase
    user_input = user_input.lower()

    # 2. split sentence into words
    words = word_tokenize(user_input)

    # 3. remove useless words (the, is, for, under...)
    filtered_words = []
    for word in words:
        if word.isalnum() and word not in stop_words:
            filtered_words.append(word)

    # 4. join important words
    cleaned_query = " ".join(filtered_words)

    return cleaned_query