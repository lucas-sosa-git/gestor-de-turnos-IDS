import os

import pymysql
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions
from pymysql.cursors import DictCursor


def get_db_connection():
    text_value = lambda value: value.decode("utf-8") if isinstance(value, bytes) else value

    conv = conversions.copy()
    conv[FIELD_TYPE.DATE] = text_value
    conv[FIELD_TYPE.TIME] = text_value
    conv[FIELD_TYPE.DATETIME] = text_value
    conv[FIELD_TYPE.TIMESTAMP] = text_value
    conv[FIELD_TYPE.DECIMAL] = float
    conv[FIELD_TYPE.NEWDECIMAL] = float

    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        conv=conv,
        cursorclass=DictCursor,
        autocommit=False,
    )