import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle


data_path = "recipes_raw_nosource_fn_train_allergen.csv" #5k rows of data categorized

data_raw = pd.read_csv(data_path)
missing_values_check = data_raw.isnull().sum()

rowSums = data_raw.iloc[:,4:].sum(axis=1)
clean_comments_count = (rowSums==0).sum(axis=0)

categories = list(data_raw.columns.values)
categories = categories[4:]

data = data_raw
data = data_raw.loc[np.random.choice(data_raw.index, size=2000)]
data.shape

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import re
nltk.download('stopwords')
import sys
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")

def cleanHtml(sentence):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', str(sentence))
    return cleantext


def cleanPunc(sentence): #function to clean the word of any punctuation or special characters
    cleaned = re.sub(r'[?|!|\'|"|#]',r'',sentence)
    cleaned = re.sub(r'[.|,|)|(|\|/]',r' ',cleaned)
    cleaned = cleaned.strip()
    cleaned = cleaned.replace("\n"," ")
    return cleaned


def keepAlpha(sentence):
    alpha_sent = ""
    for word in sentence.split():
        alpha_word = re.sub('[^a-z A-Z]+', ' ', word)
        alpha_sent += alpha_word
        alpha_sent += " "
    alpha_sent = alpha_sent.strip()
    return alpha_sent
data['ingredients'] = data['ingredients'].str.lower()
data['ingredients'] = data['ingredients'].apply(cleanHtml)
data['ingredients'] = data['ingredients'].apply(cleanPunc)
data['ingredients'] = data['ingredients'].apply(keepAlpha)
data.head()

stop_words = set(stopwords.words('english'))
stop_words.update(['zero','one','two','three','four','five','six','seven','eight','nine','ten','may','also','across','among','beside','however','yet','within','teaspoon', 'tablespoon', 'ounces', 'gallon', 'cup', 'pound', 'small','large','medium', 'chop','slice','mince','fresh','ground'])

re_stop_words = re.compile(r"\b(" + "|".join(stop_words) + ")\\W", re.I)
def removeStopWords(sentence):
    global re_stop_words
    return re_stop_words.sub(" ", sentence)

data['ingredients'] = data['ingredients'].apply(removeStopWords)

stemmer = SnowballStemmer("english")
def stemming(sentence):
    stemSentence = ""
    for word in sentence.split():
        stem = stemmer.stem(word)
        stemSentence += stem
        stemSentence += " "
    stemSentence = stemSentence.strip()
    return stemSentence

data['ingredients'] = data['ingredients'].apply(stemming)

from sklearn.model_selection import train_test_split

train_text = data['ingredients']

from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(strip_accents='unicode', analyzer='word', ngram_range=(1,3), norm='l2',max_features=25000)
vectorizer.fit(train_text)
x_train = vectorizer.transform(train_text)
y_train = data.drop(labels = ['title','ingredients','instructions','picture_link'], axis=1)

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.multiclass import OneVsRestClassifier



# Using pipeline for applying logistic regression and one vs rest classifier
LogReg_pipeline = Pipeline([
                ('clf', OneVsRestClassifier(LogisticRegression(solver='sag'), n_jobs=-1)),
            ])
    
for category in categories:
    
    # Training logistic regression model on train data
    LogReg_pipeline.fit(x_train, data[category])
    
    # calculating test accuracy
   # prediction = LogReg_pipeline.predict(x_test)
    


# using binary relevance
from skmultilearn.problem_transform import BinaryRelevance
from sklearn.naive_bayes import GaussianNB

# initialize binary relevance multi-label classifier
# with a gaussian naive bayes base classifier
classifier = BinaryRelevance(GaussianNB())

# train
classifier.fit(x_train, y_train)

# predict



real_data_path = "Grubhub.csv" #5k rows of data categorized

real_data_raw = pd.read_csv(real_data_path)
x_real = real_data_raw['transformed_desc']


pickle.dump(classifier, open('model.pkl','wb'))
model = pickle.load(open('model.pkl','rb'))
