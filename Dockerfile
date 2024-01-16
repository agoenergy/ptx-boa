FROM python:3.10-slim
LABEL version="0.2.0"

# RUN apt-get update
# RUN apt install -y git
# RUN git clone https://github.com/agoenergy/ptx-boa.git
# RUN git checkout main

WORKDIR ptx-boa
RUN pip3 install -r requirements.txt
EXPOSE 80

ENTRYPOINT ["streamlit", "run", "ptxboa_streamlit.py", "--server.port=80", "--server.address=0.0.0.0"]
