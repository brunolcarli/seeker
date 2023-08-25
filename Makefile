install:
	pip3 install -r requirements.txt

shell:
	python3 manage.py shell

server:
	python3 manage.py runserver 0.0.0.0:1025

migrate:
	python3 manage.py makemigrations
	python3 manage.py migrate

web_spider:
	python3 manage.py web_spider

amqp_consumer:
	python3 manage.py amqp_consumer
