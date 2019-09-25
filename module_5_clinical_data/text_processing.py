from nltk import word_tokenize
import re

from nltk.corpus import stopwords
import gensim


stop_words = stopwords.words('english')
headers = [
    'UNDERLYING MEDICAL CONDITION:',
    'REASON FOR THIS EXAMINATION:',
    'FINAL REPORT',
]

headers = [(re.compile(hdr.lower()), '_'.join(hdr.split(' ')).lower()) for hdr in headers]

regexes = [
#     re.compile('|'.join(headers)),
    (re.compile('clip #'), ''),
    (re.compile('[_]{3,}'), ''), # Horizontal lines
    (re.compile('\[\*\*[\d\-a-z\s\(\)]+\*\*\]'), ''), # Bracketed de-identified text 
    (re.compile('[\d]{1,2}:[\d]{1,2} (AM|PM)'), ''),
    (re.compile('[.,;:()]'), ''),
    (re.compile('[\d]+'), ''),
]


def preprocess(text):
    text = text.lower()
    for (regex, hdr) in headers:
        text = regex.sub(hdr, text)
    for (regex, sub) in regexes:
        text = regex.sub(sub, text)
    
    
    return text


def tokenize(text, rm_stopwords=True):
    tokens = word_tokenize(text)
    if remove_stopwords:
        tokens = remove_stopwords(tokens)
    return tokens

def remove_stopwords(tokens):
    return [word for word in tokens if word not in stop_words]

