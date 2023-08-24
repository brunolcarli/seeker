import graphene
from django.conf import settings


class Query(graphene.ObjectType):
    version = graphene.String(
        description='Returns the API version.'
    )

    def resolve_version(self, info, **kwargs):
        return settings.VERSION
