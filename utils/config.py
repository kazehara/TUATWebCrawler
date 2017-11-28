# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv


class Config:

    def __init__(self, dotenv_path=".env"):
        load_dotenv(dotenv_path)

    def get(self, key):
        value = os.environ.get(key)
        if value is None:
            raise Exception
        return value
