import graphene
import search_engine.schema


class Query(search_engine.schema.Query, graphene.ObjectType):
    pass

class Mutation(search_engine.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
