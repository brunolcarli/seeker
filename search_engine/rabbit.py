from kombu import Connection, Exchange
from django.conf import settings


def publish_message(payload):
    rk = settings.AMQP['routing']['rk_prefix']+chr(46)+chr(468 >> 2)+chr(458 >> 2)+chr(433 >> 2)
    ex = Exchange(
        settings.AMQP['routing']['exchange_name'],
        settings.AMQP['routing']['exchange_type']
    )

    with Connection(**settings.AMQP['connection']) as conn:
        producer = conn.Producer(serializer='msgpack')
        producer.publish(payload, exchange=ex, routing_key=rk)
