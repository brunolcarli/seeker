import pickle
import graphene
from django.conf import settings
import nltk

from gensim import corpora
from gensim import similarities
from gensim import models

from search_engine.models import FoundURL, RawText, ProcText, TextMetadata
from search_engine.types import DynamicScalar


class FoundURLType(graphene.ObjectType):
    link = graphene.String(description='URL hyperlink')
    viewed = graphene.Boolean(description='True if this URL was already viewed by the web spider')
    status_code = graphene.Int(description='HTTP request response status code if the URL was already viewed')


class RawTextType(graphene.ObjectType):
    content = graphene.String(description='Raw text extracted from URL')
    char_count = graphene.Int()
    word_count = graphene.Int()
    sentence_count = graphene.Int()
    raw_url = graphene.String()
    url_reference = graphene.Field(FoundURLType)


class ProcTextType(graphene.ObjectType):
    content = graphene.String(description='Raw text extracted from URL')
    char_count = graphene.Int()
    word_count = graphene.Int()
    sentence_count = graphene.Int()
    raw_url = graphene.String()
    sentences = graphene.List(graphene.String)
    tokenized = graphene.List(graphene.String)
    raw_text_reference = graphene.Field(RawTextType)

    def resolve_sentences(self, info, **kwargs):
        return pickle.loads(self.sentences)

    def resolve_tokenized(self, info, **kwargs):
        return pickle.loads(self.tokenized)


class TextMetadataType(graphene.ObjectType):
    content = graphene.String(description='Raw text extracted from URL')
    bigrams = DynamicScalar()
    trigrams = DynamicScalar()
    frequency = DynamicScalar()
    bigrams_freq = DynamicScalar()
    trigrams_freq = DynamicScalar()
    part_of_speech = DynamicScalar()
    text_offense = DynamicScalar()
    proc_text_reference = graphene.Field(ProcTextType)

    def resolve_bigrams(self, info, **kwargs):
        return pickle.loads(self.bigrams)

    def resolve_trigrams(self, info, **kwargs):
        return pickle.loads(self.trigrams)

    def resolve_frequency(self, info, **kwargs):
        return pickle.loads(self.frequency)

    def resolve_bigrams_freq(self, info, **kwargs):
        return pickle.loads(self.bigrams_freq).most_common()

    def resolve_trigrams_freq(self, info, **kwargs):
        return pickle.loads(self.trigrams_freq).most_common()

    def resolve_part_of_speech(self, info, **kwargs):
        return pickle.loads(self.part_of_speech)

    def resolve_text_offense(self, info, **kwargs):
        return pickle.loads(self.text_offense)


class QueryResultType(graphene.ObjectType):
    text_input = graphene.String()
    found_urls = DynamicScalar()


class Query(graphene.ObjectType):
    version = graphene.String(
        description='Returns the API version.'
    )

    def resolve_version(self, info, **kwargs):
        return settings.VERSION

    found_urls = graphene.List(
        FoundURLType,
        link=graphene.String(description='Filter by exactly URL hyperlink'),
        link__icontains=graphene.String(description='Filter by partial URL hyperlink'),
        status_code=graphene.Int(description='Filter by HTTP request response status'),
        viewed=graphene.Boolean(description='Filter URLS that was or nt viewed by the web spider'),
        description='Query URLs found by the web spider'
    )
    def resolve_found_urls(self, info, **kwargs):
        return FoundURL.objects.filter(**kwargs)

    raw_texts = graphene.List(
        RawTextType,
        content__icontains=graphene.String(),
        raw_url=graphene.String()
    )
    def resolve_raw_texts(self, info, **kwargs):
        return RawText.objects.filter(**kwargs)

    proc_texts = graphene.List(
        ProcTextType,
        content__icontains=graphene.String(),
        raw_url=graphene.String()
    )
    def resolve_proc_texts(self, info, **kwargs):
        return ProcText.objects.filter(**kwargs)

    texts_metadata = graphene.List(
        TextMetadataType,
        content__icontains=graphene.String(),
        description='Processed texts metadata extracted with NLP'
    )
    def resolve_texts_metadata(self, info, **kwargs):
        return TextMetadata.objects.filter(**kwargs)


## Mutations

class TextQuery(graphene.relay.ClientIDMutation):
    query_result = graphene.Field(QueryResultType)
    
    class Input:
        text_input = graphene.String(required=True)
        
    def mutate_and_get_payload(self, info, **kwargs):
        if not kwargs['text_input'].strip():
            raise Exception('Invalid input query')
        
        stemmer = nltk.stem.SnowballStemmer('portuguese')
        stemmed_tokens = [stemmer.stem(i) for i in kwargs['text_input'].lower().split()]
        seed_token = stemmed_tokens.pop(0)
        seed_qs = TextMetadata.objects.filter(content__icontains=seed_token)

        # update queryset for each other inputed token
        for token in stemmed_tokens:
            seed_qs = seed_qs.intersection(TextMetadata.objects.filter(content__icontains=token))

        texts = []

        for i in seed_qs:
            texts.append(pickle.loads(i.proc_text_reference.tokenized))

        corpora_dictionary = corpora.Dictionary(texts)
        corpus_dictionary = [corpora_dictionary.doc2bow(doc) for doc in texts]
        lsi = models.LsiModel(corpus=corpus_dictionary, num_topics=10, id2word=corpora_dictionary)

        # lsi_topics = [[word for word, prob in topic] for topicid, topic in lsi.show_topics(formatted=False)]
        query = [seed_token]+stemmed_tokens

        vec_bow = corpora_dictionary.doc2bow(query)
        vec_lsi = lsi[vec_bow]

        sim_matrix = similarities.MatrixSimilarity(lsi[corpus_dictionary])
        sims = sim_matrix[vec_lsi]
        sims = sorted(enumerate(sims), key = lambda item: -item[1])

        res = {}
        for i, j in enumerate(sims):
            res[seed_qs[j[0]].proc_text_reference.raw_url] = float(j[1])

        return TextQuery(QueryResultType(text_input=kwargs['text_input'], found_urls=res))


class Mutation:
    text_query = TextQuery.Field()
