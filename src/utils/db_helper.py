#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals
import sqlite3
import os
from sqlite3 import Error
from logger import log


def create(db_file):
    """
    create a database connection to the SQLite database
    specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def create_table(conn, create_table_sql):
    """
    create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_all_tabels(conn):
    """
    Creates the Database tables if not exists
    :param conn: the Connection Object
    """
    sql_create_index_table = """ CREATE TABLE IF NOT EXISTS hashes (
    path text NOT NULL,
    hash text NOT NULL,
    ignore integer DEFAULT 0 NOT NULL,
    size ineger NOT NULL,
    modified_date integer NOT NULL
    ); """

    sql_create_moved_table = """ CREATE TABLE IF NOT EXISTS moved (
    path text NOT NULL,
    hash text NOT NULL,
    ignore integer DEFAULT 0 NOT NULL,
    size ineger NOT NULL,
    modified_date integer NOT NULL
    ); """

    # create projects table
    create_table(conn, sql_create_index_table)
    create_table(conn, sql_create_moved_table)


def close(conn):
    """
    Close an open connection
    :param conn: the Connection Object
    """
    conn.close()


def commit(conn):
    """
    commit changes
    :param conn: the Connection Object
    """
    conn.commit()


def get_all_entries(conn):
    """
    Query all hash entries
    :param conn: the Connection object
    :return: List of entrries
    """

    cur = conn.cursor()
    cur.execute("SELECT * FROM hashes")

    rows = cur.fetchall()

    result = []
    for row in rows:
        result.append({
            "path": row[0],
            "hash": row[1],
            "ignore": row[2],
            "size": row[3],
            "modified_date": row[4]
        })
    return result


def get_entry_by_path(conn, path):
    """
    Query the hash entry with the same path
    :param conn: the Connection object
    :param path: a path string
    :return: First Entry with matching path or None
    """

    cur = conn.cursor()
    cur.execute("SELECT * FROM hashes WHERE path = ?", (path,))

    row = cur.fetchone()
    if row is None:
        return None
    result = {
        "path": row[0],
        "hash": row[1],
        "ignore": row[2],
        "size": row[3],
        "modified_date": row[4]
    }
    return result


def delete_by_path(conn, path):
    """
    Delete the hash entry with the same path
    :param conn: the Connection object
    :param path: a path string
    """

    cur = conn.cursor()
    cur.execute("DELETE FROM hashes WHERE path = ?", (path,))


def does_entry_exist(conn, path):
    """
    Query if there exist an entry with the same path
    :param conn: the Connection object
    :param path: a path string
    :return: True or False
    """

    cur = conn.cursor()
    cur.execute("SELECT rowid FROM hashes WHERE path = ?", (path,))

    row = cur.fetchone()
    if row is None:
        return False
    return True


def insert_entry(conn, entry):
    """
    Insert an entry into the hash dataase
    :param conn: the connection Object
    :param entry: an entry dictonary with all data
    :return: False if there is already an entry with the same path
    """
    if does_entry_exist(conn, entry["path"]):
        return False

    cur = conn.cursor()
    cur.execute("""insert into hashes(path, hash, size,
    modified_date) values(?, ?, ?, ?)""",
                (entry["path"], entry["hash"],
                 entry["size"], entry["modified_date"]))
    return True


def move_entry(conn, entry):
    """
    Moves an entry into the moved database
    :param conn: the connection Object
    :param entry: an entry dictonary with all data of the moved entry
    :return: False if there is not such an entry in the database
    """
    if not does_entry_exist(conn, entry["path"]):
        return False

    cur = conn.cursor()
    cur.execute("""insert into moved(path, hash, size,
    modified_date) values(?, ?, ?, ?)""",
                (entry["path"], entry["hash"],
                 entry["size"], entry["modified_date"]))
    delete_by_path(conn, entry["path"])
    return True


def checkConsistence(fileList, database):
    """
    Checks the consistens of a database,
    if files does not exist, they are moved
    :param fileList: a list of files from walker
    :param database: path to the database
    """
    conn = create(database)
    countFound = 0
    entries = get_all_entries(conn)
    moves = {}

    for entry in entries:
        found = False
        for file in fileList:
            if file["path"] == entry["path"]:
                countFound += 1
                found = True
                break

        if not found:
            fileBasePath = os.path.dirname(file["path"])
            if fileBasePath not in moves:
                moves[fileBasePath] = 1
            else:
                moves[fileBasePath] += 1
            move_entry(conn, entry)

    commit(conn)
    close(conn)
    countMoves = 0
    for move, count in moves:
        log("%d files in %s no longer exist!" % (count, move), 1)
        countMoves += count
    log("In total %d files no longer exist." % countMoves, 1)
    log("%d files files have already been indexed." % countFound, 5)
    log("At least %d new files must be indexed." %
        (len(fileList) - countFound), 2)


def tests():
    database = "./test.db"

    # create a database connection
    conn = create(database)
    if conn is not None:
        # create  tables
        create_all_tabels(conn)

        test_entry = {
            "path": "/lols/",
            "hash": "1asdadsdf2d312",
            "size": "12",
            "modified_date": "123123"
        }

        # insert data
        insert_entry(conn, test_entry)
        insert_entry(conn, test_entry)

        # save data
        commit(conn)

        # get all data
        entries = get_all_entries(conn)
        print(entries)

        # get specified data
        entry = get_entry_by_path(conn, "/lols/")
        print(entry)

        # check if data exists
        exists = does_entry_exist(conn, "/lols/")
        print(exists)

        close(conn)
    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    tests()
