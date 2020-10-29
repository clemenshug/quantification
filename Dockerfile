FROM python:3.6

RUN /bin/bash -c 'pip install h5py pandas numpy pathlib; \
python -m pip install git+https://github.com/scikit-image/scikit-image@636592aaf88eaec6fdc5b60fa676b55ba28fcf7d'

COPY . /app/
