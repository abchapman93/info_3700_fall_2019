import sys
from nltk.corpus import stopwords
stop_words = stopwords.words('english')
import pymysql
import pickle

from gensim.models import Word2Vec

import gensim.corpora as corpora

import text_processing

USERNAME = 'jovyan'
HOST = "35.233.174.193"
DB = 'mimic2'

def query_mimic_documents(user, pwd, host, db, limit=None):
    conn = pymysql.connect(host=host, port=3306,
                           user=user, passwd=pwd,
                           db=db)
    cursor = conn.cursor()
    query = """
        select text from noteevents
        where category = 'RADIOLOGY_REPORT'
    """
    if limit is not None:
        query += 'limit {}'.format(limit)
    cursor.execute(query)
    documents = [tup[0] for tup in cursor.fetchall()]
    print("Retrieved {} radiology reports".format(len(documents)))
    conn.close()
    return documents

def process_texts(texts):
    sentences = create_sentences(texts)
    preprocessed_sents = [text_processing.preprocess(sent) for sent in sentences]
    tokenized_sents = [text_processing.tokenize(sent, rm_stopwords=True) for sent in preprocessed_sents]
    tokenized_sents = text_processing.make_bigrams(tokenized_sents)
    return tokenized_sents

def create_sentences(texts):
    sents = []
    for text in texts:
        sents += text_processing.tokenize_sents(text)
    return sents

def save_model(word2vec, version):
    outpath = './trained_word2vec_py{}.pkl'.format(version)
    with open(outpath, 'wb') as f:
        pickle.dump(word2vec, f)
    print("Saved model at {}".format(outpath))


def main():
    rad_reports = query_mimic_documents(USERNAME, pwd, HOST, DB, limit)
    tokenized_texts = process_texts(rad_reports)
    word2vec = Word2Vec(tokenized_texts)

    # Sanity check
    print(word2vec.wv.most_similar(['pneumonia', 'infiltrate', 'infiltrates', 'consolidation'], topn=20))

    save_model(word2vec, python_version)


if __name__ == '__main__':
    pwd = sys.argv[1]
    limit = None
    # See if we're running Python 2 or 3
    python_version = sys.version_info[0]

    print("Running Python version {0}.{1}.{2}".format(*sys.version_info))

    main()

