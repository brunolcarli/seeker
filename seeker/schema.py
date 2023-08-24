import graphene
import search_engine.schema


class Query(search_engine.schema.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
