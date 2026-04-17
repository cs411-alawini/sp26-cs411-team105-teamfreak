import mysql.connector
from mysql.connector import Error

from api.config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def fetch_all_raw(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def execute_write(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def execute_many(query, params_list):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.executemany(query, params_list)
        connection.commit()
    finally:
        cursor.close()
        connection.close()
