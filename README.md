# PtX-BOA: PtX Business Opportunity Analyzer

PtX-BOA is a tool that aims to promote the export of a wide range of PtX molecules, including amongst others, green ammonia, e-methanol and synthetic fuels. Users can calculate the delivered cost of PtX molecules from an export country to an import country, with a detailed cost breakdown comparison highlighting the competitive edge of one country against another.

## Development

### Setup

Set up conda environment and install local pre-commit hooks

```bash
conda env create --file environment.yml
conda activate ptx-boa
conda env update --prune --file environment.yaml
pre-commit install
```

## Deployment

### Create image and publish to docker hub

```bash
docker build -t wingechr/ptx-boa:0.0.1 .
docker push wingechr/ptx-boa:0.0.1
```

### Run (in cloud or locally)

```bash
docker run -p 80:80 wingechr/ptx-boa:0.0.1
```
