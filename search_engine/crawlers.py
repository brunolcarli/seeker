import logging
import requests
from bs4 import BeautifulSoup
from search_engine.models import FoundURL
from search_engine.rabbit import publish_message


LOGGER = logging.getLogger(__name__)


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

        publish_message({
            'url': target_url.link,
            'status_code': target_url.status_code,
            'viewed': target_url.viewed
        })
        target_url = next(seeds, None)

    LOGGER.info('Finished weaving for this iteration')
