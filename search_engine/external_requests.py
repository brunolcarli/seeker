import requests
from django.conf import settings

class RequestLISA:
    """
    Request data process to LISA NLP API
    Requests send text input.
    Payload is a graphql query.
    Response received is as json
    """

    @staticmethod
    def request_part_of_speech(text):
        payload = f'''
        query pos {{
            partOfSpeech(text: "{text}") {{
                token
                tag
                description
            }}
        }}
        '''
        response = requests.post(settings.LISA_URL, json={'query': payload}).json()
        if 'errors' in response:
            return []
        return response['data'].get('partOfSpeech', [])

    @staticmethod
    def request_text_offense_level(text):
        payload = f'''
        query off{{
            textOffenseLevel(text: "{text}") {{
                average
                isOffensive
            }}
        }}
        '''
        response = requests.post(settings.LISA_URL, json={'query': payload}).json()
        if 'errors' in response:
            return {}
        return response['data'].get('textOffenseLevel', {})
