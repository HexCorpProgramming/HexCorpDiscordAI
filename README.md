# HexCorp Mxtress AI

## Requirements
- Python 3
- pip
- python-setuptools
- discord.py ~= 1.2.5

To install all Python dependencies you can use pip. Just enter `pip install -r requirements.txt` in the project directory.

Note: If both Python 2 and Python 3 are installed on your machine, you probably have to use `python3` and `pip3` to call version 3 explicitly.

## Deployment
To start the bot you can enter
```
python ai.py <access_token>
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