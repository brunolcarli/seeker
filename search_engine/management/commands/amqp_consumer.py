import uuid
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin
from search_engine.daemon_processors import process_url_message, process_raw_text_message, process_proc_text_message


LOGGER = logging.getLogger(__name__)


class RabbitConsumer(ConsumerMixin):
    def __init__(self, connection, queues):
        self.connection = connection
        self.queues = queues

    def get_consumers(self, Consumer, channel):
        url_consumer = Consumer(
            queues=self.queues[0],
            callbacks=[self.on_url],
            on_decode_error=self.on_decode_error,
            accept=['msgpack'],
            tag_prefix='URLS||seeker_consumer'+str(uuid.uuid4()),
            prefetch_count=10
        )
        raw_consumer = Consumer(
            queues=self.queues[1],
            callbacks=[self.on_raw],
            on_decode_error=self.on_decode_error,
            accept=['msgpack'],
            tag_prefix='RAW_TEXT||seeker_consumer'+str(uuid.uuid4()),
            prefetch_count=10
        )
        proc_consumer = Consumer(
            queues=self.queues[2],
            callbacks=[self.on_proc],
            on_decode_error=self.on_decode_error,
            accept=['msgpack'],
            tag_prefix='PROC_TEXT||seeker_consumer'+str(uuid.uuid4()),
            prefetch_count=10
        )
        
        return [url_consumer, raw_consumer, proc_consumer]
  
    def on_url(self, body, message):
        LOGGER.info('received %s from URLS', str(body))
        # message.ack()

    def on_raw(self, body, message):
        LOGGER.info('received %s from RAW_TEXT', str(body))
        # message.ack()

    def on_proc(self, body, message):
        LOGGER.info('received %s from PROC_TEXT', str(body))
        # message.ack()


class Command(BaseCommand):

    def handle(self, *args, **options):

        exchange = Exchange(
            settings.AMQP['routing']['exchange_name'],
            settings.AMQP['routing']['exchange_type']
        )

        urls_rk = settings.AMQP['routing']['rk_prefix']+chr(46)+chr(468 >> 2)+chr(458 >> 2)+chr(433 >> 2)
        raw_rk = settings.AMQP['routing']['rk_prefix']+chr(46)+''.join(chr(i>>2) for i in [456, 388, 476, 380, 464, 404, 480, 467])
        proc_rk = settings.AMQP['routing']['rk_prefix']+chr(46)+''.join(chr(i>>2) for i in [451, 459, 447, 399, 383, 467, 407, 483, 467])

        urls_queue = Queue(
            'URLS',
            exchange=exchange,
            bindings=[urls_rk],
            no_declare=True
        )
        raw_text_queue = Queue(
            'RAW_TEXT',
            exchange=exchange,
            bindings=[raw_rk],
            no_declare=True
        )
        proc_text_queue = Queue(
            'PROC_TEXT',
            exchange=exchange,
            bindings=[proc_rk],
            no_declare=True
        )

        queues = [urls_queue, raw_text_queue, proc_text_queue]
        with Connection(**settings.AMQP['connection']) as conn:
            LOGGER.info('Initializing message consumption with the following config:')
            for q in queues:
                LOGGER.info('Queue: %s', str(q.name))
            consumer = RabbitConsumer(conn, queues)
            consumer.run()
