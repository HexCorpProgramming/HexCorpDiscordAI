# HexCorp Mxtress AI

## Requirements
- Python 3.8
- pip
- python-setuptools
- discord.py ~= 1.2.5

To install all Python dependencies you can use pip. Just enter `pip install -r requirements.txt` in the project directory.

Note: We use Python 3.8+ so if your system does have multiple versions installed you may have to specify which installation to use e.g. `python3.8` and `pip3.8`.

## Deployment
To start the bot you can enter
```
python3.8 ai.py <access_token>
```
in the project directory.

### Current server configuration

#### Update
To update the current production instance of the AI you have to:
1. kill the running process
2. navigate into the project repo
3. `git fetch`
4. `git checkout <NEW_VERSION>`
5. navigate back up
6. `sh start_ai.sh`

## Hints for development
### Database
We use a SQLite DB to persist certain data. It is recommended to get a SQL client so you can poke around in it.

When you want to change the DB schema, you can create a new sql-file in `res/db/migrate`. The number in the beginning has to be higher then every other number of the migration scripts. These scripts are executed in sequence when the AI starts.

If you manage to screw up your DB you can remove it by simply deleting the file `ai.db`. On the next AI start the DB will be recreated.

## CI
### Linting
We use flake8 as a linting tool. Everytime you push code, our CI-pipeline will run flake8 to find problems and will notify you if stuff should be changed. If you want to run flake8 yourself, you can use `pip install flake8` to install it and then simply call `flake8` at the project root.

It is also recommended to configure flake8 as your IDE linting tool, to get your code highlighted.