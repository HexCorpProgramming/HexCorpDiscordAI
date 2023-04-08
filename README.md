# HexCorp Mxtress AI

## Requirements

- Python 3.11
- pip
- python-setuptools
- pycord 2.4.1

To install all Python dependencies you can use pip. Just enter
`pip install -r requirements.txt` in the project directory.

Note: We use Python 3.11+ so if your system does have multiple versions
installed, you may have to specify which installation to use e.g.
`python3.11` and `pip3.11`.

## Building and deploying with Docker

### Building

To build a Docker image, simply invoke:

``` bash
docker image build --tag mxtress_ai:latest .
```

### Running

Running the Discord bot in a Docker container is simple, though care must be
given to expose the Discord API key and bot database to the runtime.  Assuming
the `ai.db` file is present in the current working directory, run the following:

``` bash
docker run \
    --name HiveMxtressAI \
    --detach \
    --restart always \
    --env DISCORD_ACCESS_TOKEN=(bot token) \
    --volume ai.db:/var/opt/HexCorpDiscordAI/ai.db \
    mxtress_ai:latest
```

## Building and running with system Python

To start the bot you can enter the following command in the project root:

```bash
python3.11 main.py <access_token>
```

### Updating

To update the current production instance of the AI you have to:

1. Kill the running process
2. Navigate into the project repo
3. `git fetch`
4. `git checkout <NEW_VERSION>`
5. `cd ..`
6. `sh start_ai.sh`

## Tips for development

### Database

The Discord bot uses an SQLite3 database to persist runtime data.  A graphical
database client is recommended to easily view its contents.

When performing database schema changes, create a new SQL file in the
`res/db/migrate/` directory.  The schema filename should adhere to the naming
convention therein, with an incremented four-digit sequence number.  Any schema
files which have not been applied yet will be applied in ordered sequence when
starting the bot.

In the event of database corruption, simply remove the `ai.db` file; the
database will be recreated with the `res/db/migrate/` schema files the next time
the bot is started.

### Linting and syntax highlighting

The Python tool `flake8` is used to lint the codebase.  To perform linting
locally, one may install the tool using `pip3 install flake8`; invoking it is
as simple as running `flake8` in the project root.

If using an IDE for development, it is highly recommended to set up flake8 to
benefit from syntax highlighting.

## Continuous integration

All commits pushed to the repository upstream pass through GitHub's continuous
integration pipeline, as per the file `.github/workflows/continuous-integration.yml`.
The project will go through the following stages in the pipeline:

1. The codebase will be linted with `flake8`.
2. Unit tests will be invoked with the `run_tests_with_coverage.sh` script.
3. The unit test coverage metrics from the above step will be measured; 60%
   coverage of the codebase must be met .

All steps must pass in order for a commit to be accepted.
