FROM python:3.10-slim
LABEL version="0.1.2"

RUN apt-get update
RUN apt-get install -y git
RUN git clone https://github.com/agoenergy/ptx-boa.git
RUN git checkout main

WORKDIR ptx-boa
RUN pip3 install -r requirements.txt
EXPOSE 80

ENTRYPOINT ["streamlit", "run", "ptxboa_streamlit.py", "--server.port=80", "--server.address=0.0.0.0"]
