from flask import Flask,render_template,url_for,request,send_file,redirect
import time
import spacy
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lsa import LsaSummarizer

from spacy_summarization import text_summarizer
from gensim.summarization import summarize
from nltk_summarization import nltk_summarizer

from bs4 import BeautifulSoup
##from flask_uploads import UploadSet,configure_uploads,ALL,DATA
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from heapq import nlargest
import re
import os
from werkzeug.utils import secure_filename
nlp = spacy.load('en_core_web_lg')
from spacy.lang.en.stop_words import STOP_WORDS
stopwords = list(STOP_WORDS)
from string import punctuation

nlp = spacy.load("en_core_web_sm")
timestr = time.strftime("%Y%m%d-%H%M%S")

app = Flask(__name__)
#here i used Web Scraping Pkg
from bs4 import BeautifulSoup
# instead of this  -- from urllib.request import urlopen i used urllib.request only
import urllib.request

#summarizer
def summariser_spacy(raw_docx):
    raw_text = raw_docx
    docx = nlp(raw_text)
    stopwords = list(STOP_WORDS)
    word_frequencies = {}  
    for word in docx:  
        if word.text not in stopwords:
            if word.text not in word_frequencies.keys():
                word_frequencies[word.text] = 1
            else:
                word_frequencies[word.text] += 1

    maximum_frequncy = max(word_frequencies.values())

    for word in word_frequencies.keys():  
        word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
    sentence_list = [ sentence for sentence in docx.sents ]

    sentence_scores = {}  
    for sent in sentence_list:  
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if len(sent.text.split(' ')) < 100:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word.text.lower()]
                    else:
                        sentence_scores[sent] += word_frequencies[word.text.lower()]

    summary_sentences = nlargest(30, sentence_scores, key=sentence_scores.get)
    final_sentences = [ w.text for w in summary_sentences ]
    summary = ' '.join(final_sentences)
    return(summary)

#cleaning function
def clean_text(t1):
    t1=re.sub(r'\[[0-9]*\]',' ',t1)#removing brackets and extra spaces
    t1=re.sub(r'\s+',' ',t1)
    t2=t1
    t2=re.sub('[^a-zA-Z]',' ',t1)#removing special characters and digits
    t2=re.sub(r'\s+',' ',t1)
    return t2

# Fetch Text From Url
def text_from_url(URL):
    article=urllib.request.urlopen(URL)
    parsed_article=BeautifulSoup(article,'html')
    paragraphs=parsed_article.find_all('p')
    article_text=" "
    for p in paragraphs:
        article_text += p.text
    return(str(article_text))

@app.route('/url_text',methods=['GET','POST'])
def url_text():
    if request.method == 'POST':
        raw_url = request.form['raw_url']
        raw_text = text_from_url(raw_url)
        cleaned_text = clean_text(raw_text)
        summary_scraped = summariser_spacy(cleaned_text)
        return render_template('index2.html',summary_scraped=summary_scraped)


@app.route('/about')
def about():
    return render_template('index.html')

def luhn_summary(docx):
	parser = PlaintextParser.from_string(docx,Tokenizer("english"))
	summarizer_luhn = LuhnSummarizer()
	summary_1 =summarizer_luhn(parser.document,2)
	summary_list = [str(sentence) for sentence in summary_1]
	result = ' '.join(summary_list)
	return result

def lsa_summary(docx):
   parser = PlaintextParser.from_string(docx,Tokenizer("english"))
   summarizer_lsa = LsaSummarizer()
   summary_2 =summarizer_lsa(parser.document,3)
   summary_list = [str(sentence) for sentence in summary_2]
   result = ' '.join(summary_list)
   return result


def readingTime(mytext):
	total_words = len([ token.text for token in nlp(mytext)])
	estimatedTime = total_words/200.0
	return estimatedTime

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/process',methods=['GET','POST'])
def process():
    start = time.time()
    if request.method == 'POST':
        input_text = request.form['input_text']
        model_choice = request.form['model_choice']
        final_reading_time = readingTime(input_text)
        if model_choice == 'default':
            final_summary = luhn_summary(input_text)
        elif model_choice == 'lex_summarizer':
            final_summary = lex_summary(input_text)
        elif model_choice == 'luhn_summarizer':
            final_summary= luhn_summary(input_text)
        elif model_choice == 'lsa_summarizer':
            final_summary= lsa_summary(input_text)
    summary_reading_time = readingTime(final_summary)
    end = time.time()
    final_time = end-start
    return render_template('result.html',ctext=input_text,final_reading_time=final_reading_time,summary_reading_time=summary_reading_time,final_summary=final_summary,model_selected=model_choice)

@app.route('/index2',methods = ['POST', 'GET'])
def result_pdff():
	if request.method == 'POST':
		f = request.files['file']
		f.save(secure_filename(f.filename))
		from abberivator_flow import document_abberivator as da
		out_text_file = open('out.pdf', 'w')
		out_text_file.write(da.summarize(f.filename))
		out_text_file.close()
		return send_file('c:\\users\\new\\appData\\roaming\\python\\python38\\scripts\\flask_app\\out.txt', as_attachment=True)

# Sumy 
def sumy_summary(docx):
	parser = PlaintextParser.from_string(docx,Tokenizer("english"))
	lex_summarizer = LexRankSummarizer()
	summary = lex_summarizer(parser.document,3)
	summary_list = [str(sentence) for sentence in summary]
	result = ' '.join(summary_list)
	return result
    
    
    
@app.route('/compare_summary')
def compare_summary():
	return render_template('compare_summary.html')

@app.route('/comparer',methods=['GET','POST'])
def comparer():
	start = time.time()
	if request.method == 'POST':
            input_text = request.form['input_text']
            final_reading_time = readingTime(input_text)
            final_summary_spacy = text_summarizer(input_text)
            summary_reading_time = readingTime(final_summary_spacy)
            final_summary_gensim = summarize(input_text)
            summary_reading_time_gensim = readingTime(final_summary_gensim)
            final_summary_nltk = nltk_summarizer(input_text)
            summary_reading_time_nltk = readingTime(final_summary_nltk)
            final_summary_sumy = sumy_summary(input_text)
            summary_reading_time_sumy = readingTime(final_summary_sumy)
            final_summary_luhn = luhn_summary(input_text)
            summary_reading_time_luhn = readingTime(final_summary_luhn)
            final_summary_lsa = lsa_summary(input_text)
            summary_reading_time_lsa = readingTime(final_summary_lsa)
            end = time.time()
            final_time = end-start
	return render_template('compare_summary.html',ctext=input_text,final_summary_spacy=final_summary_spacy,final_summary_gensim=final_summary_gensim,final_summary_nltk=final_summary_nltk,final_time=final_time,final_reading_time=final_reading_time,summary_reading_time=summary_reading_time,summary_reading_time_gensim=summary_reading_time_gensim,final_summary_sumy=final_summary_sumy,final_summary_luhn=final_summary_luhn,final_summary_lsa=final_summary_lsa,summary_reading_time_sumy=summary_reading_time_sumy,summary_reading_time_nltk=summary_reading_time_nltk,summary_reading_time_luhn=summary_reading_time_luhn,summary_reading_time_lsa=summary_reading_time_lsa)

if __name__ == '__main__':
	app.run(debug=True)
    
    
    
    
    
    
    
