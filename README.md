# PtX-BOA: PtX Business Opportunity Analyser

PtX-BOA is a tool that aims to promote the export of a wide range of PtX molecules, including amongst others, green ammonia, e-methanol and synthetic fuels. Users can calculate the delivered cost of PtX molecules from an export country to an import country, with a detailed cost breakdown comparison highlighting the competitive edge of one country against another.

## Development

### Setup

After cloning the repository, create a virtual python environment
in a subdirectory `.env` and activate it:

```bash
python -m venv .\.env
.env\Scripts\activate.bat
```

Install the necessary dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
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

### Download optimization cache for local development

````bash
cd ptxboa\cache
scp -r ptxboa2:ptx-boa_offline_optimization/optimization_cache/* .
````

## Release Procedure

- merge all relevant branches into develop
- create a relase branch
- change and commit `CHANGELOG.md` with description of changes
- update version (`bumpversion patch|minor|major`).
  This creates automatically a commit
- create pull requests to merge release into main
- merging this will automatically (via git action) create
  and publish the new docker image `wingechr/ptx-boa:<VERSION>`
- merge main back into develop

### Update docker image in production

```bash
# connect to server
ssh ptxboa
# pull latest image from dockerhub
VERSION=2.1.1
docker pull wingechr/ptx-boa:$VERSION
# stop and delete the currently running container "app"
docker stop app
docker rm app
# start the latest image as "app"
docker run -d -p 9000:80 -v /home/ptxboa/ptx-boa_offline_optimization/optimization_cache:/mnt/cache --name app --restart unless-stopped wingechr/ptx-boa:$VERSION

# see logs
docker logs --follow app
```

### Cleanup docker images from old versions
```bash
# check which docker images are downloaded
docker image ls
# if there is an old image present (let's assume from v0.6.0), you can delete it with:
docker image rm wingechr/ptx-boa:0.6.0
```
