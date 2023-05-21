FROM python:3.11.3-slim-bullseye

COPY requirements.txt /root
RUN pip3 install -r /root/requirements.txt

WORKDIR /var/opt/HexCorpDiscordAI

COPY main.py .
COPY src/ ./src/
COPY res/ ./res/

CMD python3.11 main.py ${DISCORD_ACCESS_TOKEN}
