FROM python:3.8.16-slim-bullseye

COPY requirements.txt /root
RUN pip3 install -r /root/requirements.txt

WORKDIR /var/opt/HexCorpDiscordAI

COPY . .

CMD python3.8 main.py ${DISCORD_ACCESS_TOKEN}
