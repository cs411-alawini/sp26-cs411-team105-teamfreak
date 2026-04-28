from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from api.config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def transaction():
    connection = get_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


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


def call_procedure(name, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        placeholders = ", ".join(["%s"] * len(params or []))
        cursor.execute(f"CALL {name}({placeholders})", params or ())
        results = []
        while True:
            results.append(cursor.fetchall())
            if not cursor.nextset():
                break
        return results
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
