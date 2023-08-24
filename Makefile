install:
	pip3 install -r requirements.txt

shell:
	python3 manage.py shell

server:
	python3 manage.py runserver 0.0.0.0:1025
