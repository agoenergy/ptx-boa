# PtX-BOA: PtX Business Opportunity Analyzer

PtX-BOA is a tool that aims to promote the export of a wide range of PtX molecules, including amongst others, green ammonia, e-methanol and synthetic fuels. Users can calculate the delivered cost of PtX molecules from an export country to an import country, with a detailed cost breakdown comparison highlighting the competitive edge of one country against another.

## Development

### Setup

After cloning the repository, create a virtual python environment
in a subdirectory `.env` and activate it:

```bash
$ python -m venv .\.env
$ .env\Scripts\activate.bat
```

Install the necessary dependencies:

```bash
$ python -m pip install --upgrade pip
$ pip install -r requirements-dev.txt
```

The code is autoformatted and checked with [pre-commit](https://pre-commit.com/).
If you make changes to the code that you want to commit back to the repository,
please install pre-commit with:

```bash
pre-commit install
```

If you have pre-commit installed, every file in a commit is checked to match a
certain style and the commit is stopped if any rules are violated. Before committing,
you can also check your staged files manually by running:

```bash
pre-commit run
```

In order to run the tests locally run [pytest](https://pytest.org) in the root directory:

```bash
pytest
```

## Deployment

### Create image and publish to docker hub

```bash
bumpversion patch|minor|major
docker build -t wingechr/ptx-boa:<VERSION>.
docker push wingechr/ptx-boa:<VERSION>
```

### Deploy in production

```bash
docker pull wingechr/ptx-boa:<VERSION>
docker images
docker container ls --all
docker ps --no-trunc

docker stop app
docker rm app
docker run -d -p 9000:80 --name app --restart unless-stopped wingechr/ptx-boa:<VERSION>
```
