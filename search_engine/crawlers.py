import logging
import pickle
import requests
from string import punctuation
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from search_engine.models import FoundURL, RawText, ProcText, TextMetadata
from search_engine.rabbit import publish_message
from search_engine.external_requests import RequestLISA



LOGGER = logging.getLogger(__name__)
STEMMER = nltk.stem.SnowballStemmer('portuguese')
STOPW = set(stopwords.words())

def web_weave():
    seeds = FoundURL.objects.filter(viewed=False)
    LOGGER.info(f'(Re)starting web weaving with {seeds.count()} targets.')
    seeds = seeds.iterator()
    target_url = next(seeds, None)
    while target_url is not None:
        LOGGER.info('Requesting %s', target_url.link)
        try:
            response = requests.get(target_url.link, timeout=15)
        except:
            LOGGER.error(f'|SPIDER|Request failed for URL: {target_url.link}')
            target_url.viewed = True
            target_url.status_code = 9999
            target_url.save()

            # pop new target URL and go to the start of the loop
            target_url = next(seeds, None)
            continue

        # if the request was not OK update target URL and go to the start of the loop
        if response.status_code != 200:
            LOGGER.error(f'|SPIDER|Request failed for URL: {target_url.link}')
            target_url.viewed = True
            target_url.status_code = response.status_code
            target_url.save()

            # pop new target URL and go to the start of the loop
            target_url = next(seeds, None)
            continue

        # grab all existent url htperlinks from page HTML
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        found_urls = [i.attrs.get('href') for i in soup.find_all('a') if i.attrs.get('href', '').startswith('http')]
        LOGGER.info('Found %s links at %s', str(len(found_urls)), target_url.link)
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
        LOGGER.info(f'|Crawler|Request failed for URL: {url}')
        return

    soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
    texts = [i.text for i in soup.find_all(['p', 'span']) if len(i.text) > 1 and i.text.isalpha() and i.text.isascii()]
    corpus = ' '.join(texts).lower().replace('\t', '').replace('\n', ' ').strip()
    if len(corpus) <= 2:
        LOGGER.info('|Crawler|Corpus length to small')
        return

    try:
        url_from_db = FoundURL.objects.get(link=url)
    except FoundURL.DoesNotExist:
        # url_from_db = FoundURL.objects.create(link=url, viewed=True, status_code=response.status_code)
        # url_from_db.save()
        LOGGER.error('|Crawler|URL %s not found', url)
        return

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
            'reference_id': raw_text.id
        },
        rk=''.join(chr(i>>2) for i in [456, 388, 476, 380, 464, 404, 480, 467])
    )


def text_preprocess(data):
    corpus = data['content']
    # identify the stopwords on corpus
    found_stopwords = list(set(corpus.split()).intersection(STOPW))

    # Remove the found stopwords from corpus
    for sw in found_stopwords:
        corpus = corpus.replace(f' {sw} ', ' ')

    # stemm the words
    corpus = ' '.join(STEMMER.stem(i) for i in corpus.split())

    # get sentences
    sentences = nltk.sent_tokenize(corpus)
    
    # remove puncts and tokenize
    for punct in punctuation:
        corpus = corpus.replace(punct, ' ')
    tokens = nltk.tokenize.word_tokenize(corpus)

    corpus = ' '.join(i for i in tokens if len(i) >= 2)

    if len(corpus) <= 2:
        LOGGER.info('|Pre|Corpus length to small')
        return

    try:
        raw_from_db = RawText.objects.get(id=data['reference_id'])
    except RawText.DoesNotExist:
        LOGGER.error('|Pre|Raw text not found')
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
            'raw_text_reference': raw_from_db.id,
            'reference_id': proc_text.id
        },
        rk=''.join(chr(i>>2) for i in [451, 459, 447, 399, 383, 467, 407, 483, 467])
    )


def process_text_metadata(data):
    tokens = pickle.loads(data['tokenized'])
    bigrams = [i for i in nltk.bigrams(tokens)]
    trigrams = [i for i in nltk.trigrams(tokens)]
    frequency = nltk.FreqDist(tokens)
    bigrams_freq = nltk.collocations.BigramCollocationFinder.from_words(tokens).ngram_fd
    trigrams_freq = nltk.collocations.TrigramCollocationFinder.from_words(tokens).ngram_fd
    try:
        part_of_speech = RequestLISA.request_part_of_speech(' '.join(set(tokens)))
    except:
        part_of_speech = []
    try:
        text_offense = RequestLISA.request_text_offense_level(data['content'])
    except:
        text_offense = {}

    try:
        proc_text_from_db = ProcText.objects.get(id=data['reference_id'])
    except ProcText.DoesNotExist:
        LOGGER.error('|Meta|Proc text not found')
        return

    text_meta = TextMetadata.objects.create(
        content=data['content'],
        bigrams=pickle.dumps(bigrams),
        trigrams=pickle.dumps(trigrams),
        frequency=pickle.dumps(frequency),
        bigrams_freq=pickle.dumps(bigrams_freq),
        trigrams_freq=pickle.dumps(trigrams_freq),
        part_of_speech=pickle.dumps(part_of_speech),
        text_offense=pickle.dumps(text_offense),
        proc_text_reference=proc_text_from_db
    )
    text_meta.save()
