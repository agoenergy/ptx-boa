FROM ghcr.io/prefix-dev/pixi:0.70.2-bookworm
LABEL version="3.0.1"

WORKDIR ptx-boa
COPY . .
RUN pixi install -e default
EXPOSE 80
# disable progress bar
ENV TQDM_DISABLE=1
ENV HIGHS_OUTPUT_FLAG=false
ENV PTXBOA_CACHE_DIR=/mnt/cache

ENTRYPOINT ["pixi", "run", "streamlit"]
