FROM continuumio/miniconda3:4.8.2

RUN conda install -c rapidsai -c nvidia -c conda-forge -c defaults rapids=0.16 python=3.7 cudatoolkit=10.1 boto3

ENV PYTHONUNBUFFERED=TRUE
ENTRYPOINT ["python3"]
