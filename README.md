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
    --volume /absolute/path/to/the/repo/ai.db:/var/opt/HexCorpDiscordAI/ai.db \
    mxtress_ai:latest
```

## Building and running with system Python

To start the bot you can enter the following command in the project root:

```bash
python3.11 main.py <access_token>
```

## Updating

To update the current production instance of the AI you have to:

1. Kill the running process
2. Navigate into the project repo
3. `git fetch`
4. `git checkout <NEW_VERSION>`
5. `cd ..`
6. `sh start_ai.sh`

## Tips for development

### Containerised Development

To develop in a container, download the git repository and then run `code .`
to launch Visual Studio Code.  Select "Reopen in Container" when prompted.

This will build a Docker container with Python, Git, the required Python
packages, and VSCode extensions.

The project code is mounted from the host into: `/workspaces/HexCorpDiscordAI/`

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

### Logging

The global `log` object provides functions for each of the standard log levels:

- debug
- info
- warning
- error
- critical

They accept an error message as the first parameter, followed by arbitrary positional and keyword arguments to be
appended to the log message.

Internally the logger maintains a per-execution-context stack of logging contexts.  Entering a new logging context
will cause all subsequent log messages within that context to be prefixed with the context's description.

Logging contexts are stored per execution context, and so are safe to use with async functions.

Basic usage is:

```py
# Import the global logging instance.
import log from src.Log

# Log a basic message with associated data.
log.error('Something went wrong', example_data='test')
```

To add additional context information use:

```py
import LoggingContext from src.Log

# Start a new logging context with additional information.
with LoggingContext('Doing a thing...'):
    do_thing()
```

### Unit Testing

Run tests using `./run_tests_with_coverage.sh`

This project has a custom test harness called `Mocks` to mock interaction with Discord.

The `Mocks` class creates a mock guild and mock bot. Additionally created mock objects
will be automatically added to the guild where appropriate.

#### The Mocks Class

The `Mocks` class can create mocks of these objects:

- Guild
- Drone
- Channel
- CategoryChannel
- Role
- Member
- Message
- Battery Type
- DroneMember
- DroneOrder
- Storage
- Timer
- Emoji

All mock creation functions allow you to pass in arbitrary keyword parameters
to set properties on the mock, for example:

```py
member = mocks.member(display_name='Test Member')
```

There are also helper functions:

- `get_guild()`: Get the mock guild instance.
- `get_bot()`: Get the testing bot instance.
- `get_cog()`: Get the Cog command being tested.
- `hive_mxtress()`: Create a DroneMember with the Hive Mxtress role.

#### Testing Cogs

To test a Cog:

1. Use the `@cog()` decorator.
2. Create a `Member` that is the author of the command message.
2. Create a mock command message.
3. Run the command using `assert_command_successful()`
4. Perform assertions.

Using `command()` instead of `message()` automatically adds `COMMAND_PREFIX`
to the message text.

The mock `context` exposed as `mocks.get_bot().context`. This allows you to
check messages sent by `context.send()`.

Note that there was no need to patch any functions.
The `@cog` decorator patches the DroneMember parameter converter so that if
the command references any members, they are loaded from the mock guild.

```py
import unittest
from test.cog import cog
from test.mocks import Mocks
# from my_cog import MyCog

class TestMyCog(unittest.IsolatedAsyncioTestCase):

    @cog(MyCog)
    async def test_my_cog(self, mocks: Mocks):
        '''
        Test the command "hc!do_something".
        '''

        # Create the mock author of the message.
        author = mocks.member()

        # Create the message that triggers the command.
        message = mocks.command(author, 'general', 'do_something')

        # Execute the command.
        await self.assert_command_successful(message)

        # Perform assertions.
        # In this case, assert that a reply was sent.
        mocks.get_bot().context.send.assert_called_once()
```

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
