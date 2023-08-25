import logging
import pickle
import requests
from string import punctuation
from bs4 import BeautifulSoup
from search_engine.models import FoundURL, RawText, ProcText
from search_engine.rabbit import publish_message

from collections import defaultdict
from gensim import corpora
from gensim import similarities
from gensim import models
import nltk
from nltk.corpus import stopwords


LOGGER = logging.getLogger(__name__)
STEMMER = nltk.stem.SnowballStemmer('portuguese')
STOPW = set(stopwords.words())

def web_weave():
    seeds = FoundURL.objects.filter(viewed=False)
    LOGGER.info(f'(Re)starting web weaving with {seeds.count()} targets.')
    seeds = seeds.iterator()
    target_url = next(seeds, None)
    while target_url is not None:
        try:
            response = requests.get(target_url.link)
        except:
            LOGGER.info(f'|SPIDER|Request failed for URL: {target_url.link}')
            target_url.viewed = True
            target_url.status_code = 9999
            target_url.save()

            # pop new target URL and go to the start of the loop
            target_url = next(seeds, None)
            continue

        # if the request was not OK update target URL and go to the start of the loop
        if response.status_code != 200:
            target_url.viewed = True
            target_url.status_code = response.status_code
            target_url.save()

            # pop new target URL and go to the start of the loop
            target_url = next(seeds, None)
            continue

        # grab all existent url htperlinks from page HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        found_urls =[i.attrs.get('href') for i in soup.find_all('a') if i.attrs.get('href', '').startswith('http')]

        # Create new found URLs on database
        for url_found in found_urls:
            obj, created = FoundURL.objects.get_or_create(link=url_found)
            if created: obj.save()

        # update the target URL and publish the succeeded URL to AMQP exchange
        target_url.viewed = True
        target_url.status_code = response.status_code
        target_url.save()

        publish_message(
            {
                'url': target_url.link,
                'status_code': target_url.status_code,
                'viewed': target_url.viewed
            },
            rk=chr(468 >> 2)+chr(458 >> 2)+chr(433 >> 2)
        )
        target_url = next(seeds, None)

    LOGGER.info('Finished weaving for this iteration')


def web_crawler(data):
    url = data.get('url')
    try:
        response = requests.get(url)
    except:
        LOGGER.info(f'|Craler|Request failed for URL: {url}')
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    texts = [i.text for i in soup.find_all(['p', 'span']) if len(i.text) > 1]
    corpus = ' '.join(texts).lower().replace('\t', '').replace('\n', ' ').strip()
    if len(corpus) <= 2:
        return

    try:
        url_from_db = FoundURL.objects.get(link=url)
    except FoundURL.DoesNotExist:
        url_from_db = FoundURL.objects.create(link=url, viewed=True, status_code=response.status_code)
        url_from_db.save()

    sentence_count = len(nltk.sent_tokenize(corpus))
    char_count = len(corpus)
    token_count = len(corpus.split())
    raw_text = RawText.objects.create(
        content=corpus,
        char_count=char_count,
        word_count=token_count,
        sentence_count=sentence_count,
        raw_url=url,
        url_reference=url_from_db
    )
    raw_text.save()
    publish_message(
        {
            'content': corpus,
            'char_count': char_count,
            'word_count': token_count,
            'sentence_count': sentence_count,
            'raw_url': url,
            'reference_id': url_from_db.id
        },
        rk=''.join(chr(i>>2) for i in [456, 388, 476, 380, 464, 404, 480, 467])
    )


def text_preprocess(data):
    # stemm the words
    corpus = STEMMER.stem(data['content'])

    # identify the stopwords on corpus
    found_stopwords = list(set(corpus.split()).intersection(STOPW))

    # Remove the found stopwords from corpus
    for sw in found_stopwords:
        corpus = corpus.replace(sw, '')

    # get sentences
    sentences = nltk.sent_tokenize(corpus)
    
    # remove puncts and tokenize
    for punct in punctuation:
        corpus = corpus.replace(punct, ' ')
    tokens = nltk.tokenize.word_tokenize(corpus)

    if len(corpus) <= 2:
        return

    try:
        raw_from_db = RawText.objects.get(id=data['reference_id'])
    except RawText.DoesNotExist:
        return

    proc_text = ProcText.objects.create(
        content=corpus,
        char_count=len(corpus),
        word_count=len(tokens),
        sentence_count=len(sentences),
        tokenized=pickle.dumps(tokens),
        sentences=pickle.dumps(sentences),
        raw_url=data['raw_url'],
        raw_text_reference=raw_from_db
    )
    proc_text.save()
    publish_message(
        {
            'content': corpus,
            'char_count': len(corpus),
            'word_count': len(tokens),
            'sentence_count': len(sentences),
            'tokenized': pickle.dumps(tokens),
            'sentences': pickle.dumps(sentences),
            'raw_url': data['raw_url'],
            'raw_text_reference': raw_from_db.id
        },
        rk=''.join(chr(i>>2) for i in [451, 459, 447, 399, 383, 467, 407, 483, 467])
    )

