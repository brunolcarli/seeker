import pickle
import graphene
from django.conf import settings
from search_engine.models import FoundURL, RawText, ProcText



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
        content_icontains=graphene.String(),
        raw_url=graphene.String()
    )
    def resolve_raw_texts(self, info, **kwargs):
        return RawText.objects.filter(**kwargs)

    proc_texts = graphene.List(
        ProcTextType,
        content_icontains=graphene.String(),
        raw_url=graphene.String()
    )
    def resolve_proc_texts(self, info, **kwargs):
        return ProcText.objects.filter(**kwargs)