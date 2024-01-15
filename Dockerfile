FROM python:3.10-slim
LABEL version="0.1.1"

RUN apt-get update
RUN apt install -y git
RUN git clone https://github.com/agoenergy/ptx-boa.git

WORKDIR ptx-boa

RUN git checkout develop
RUN pip3 install -r requirements.txt

EXPOSE 80

ENTRYPOINT ["streamlit", "run", "ptxboa_streamlit.py", "--server.port=80", "--server.address=0.0.0.0"]
