FROM python:3.10-slim
LABEL version="2.0.0"

RUN apt-get update
RUN apt-get install -y git
RUN git clone https://github.com/agoenergy/ptx-boa.git
WORKDIR ptx-boa
RUN git checkout main
RUN pip3 install -r requirements.txt
EXPOSE 80
# disable progress bar
ENV TQDM_DISABLE=1
ENV HIGHS_OUTPUT_FLAG=false
ENV PTXBOA_CACHE_DIR=/mnt/cache

ENTRYPOINT ["streamlit", "run", "ptxboa_streamlit.py", "--server.port=80", "--server.address=0.0.0.0"]
