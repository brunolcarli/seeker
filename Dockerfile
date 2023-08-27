FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/* \
    apt-get install make \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo

RUN apt-get update && apt-get install -y python3-pip

RUN mkdir /app
WORKDIR /app

RUN python3 -m pip install --upgrade cython

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN	python3 -c "import nltk;nltk.download('punkt')"
RUN	python3 -c "import nltk;nltk.download('stopwords')"
RUN	python3 -c "import nltk;nltk.download('averaged_perceptron_tagger')"

COPY . .

RUN python3 manage.py makemigrations
RUN	python3 manage.py migrate


ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV NAME seeker