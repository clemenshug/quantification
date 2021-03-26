FROM python:3.6

RUN /bin/bash -c 'pip install h5py pandas numpy pathlib; \
python -m pip install \'scikit-image>=0.18.0\''

COPY . /app/
