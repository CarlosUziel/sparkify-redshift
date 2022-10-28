import logging
from pathlib import Path
from typing import Any

import psycopg2

from sql_queries import (
    STAGING_TABLES,
    STAR_TABLES,
    STAR_TABLES_CONSTRAINTS,
    STAR_TABLES_DISTSTYLES,
    get_create_table_query,
    get_drop_table_query,
)
from utils import get_db_connection, process_config


def drop_tables(cur: Any, conn: Any):
    """Drop staging, fact and dimension tables"""
    for table_name in [*STAR_TABLES.keys(), *STAGING_TABLES.keys()]:
        cur.execute(get_drop_table_query(table_name))
        conn.commit()


def create_tables(cur: Any, conn: Any):
    """Create staging, fact and dimension tables"""
    for table_name, table_args in [*STAR_TABLES.items(), *STAGING_TABLES.items()]:
        cur.execute(
            get_create_table_query(
                table_name, [*table_args, *STAR_TABLES_CONSTRAINTS.get(table_name, [])]
            )
            + f" {STAR_TABLES_DISTSTYLES.get(table_name, '')}"
        )
        conn.commit()


def main():
    # 0. Get configuration parameters
    dwh_config = process_config(Path(__file__).parents[1].joinpath("dwh.cfg"))

    # 1. Get connection and cursor
    conn, cur = get_db_connection(dwh_config)

    # 2. Drop and create tables
    try:
        drop_tables(cur, conn)
        create_tables(cur, conn)
    except psycopg2.Error as e:
        logging.error(f"Error dropping/creating tables: \n{e}")

    # 3. Close connection
    conn.close()


if __name__ == "__main__":
    main()
