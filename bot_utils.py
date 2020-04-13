import discord
import re

def get_id(username: str):
    return re.search(r"\d{4}", username).group()