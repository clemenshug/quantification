FROM python:3.9

RUN /bin/bash -c 'pip install h5py pandas numpy pathlib pip install scikit-image>=0.18.0';

COPY . /app/
