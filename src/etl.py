import logging
from configparser import ConfigParser
from pathlib import Path
from typing import Any

import psycopg2
from tqdm.rich import tqdm

from sql_queries import STAGING_TABLES, STAR_TABLES_INSERTS, get_copy_s3_query
from utils import get_db_connection, process_config


def load_staging_tables(cur: Any, conn: Any, dwh_config: ConfigParser):
    """Load staging tables from .json files stored in a S3 bucket"""
    for table_name in (pbar := tqdm(STAGING_TABLES.keys())):
        pbar.set_description(f"Inserting data into {table_name}...")
        cur.execute(
            get_copy_s3_query(
                table_name,
                (
                    dwh_config.get("S3", "song_data")
                    if table_name == "staging_songs"
                    else dwh_config.get("S3", "log_data")
                ),
                dwh_config.get("DWH", "dwh_role_arn"),
                dwh_config.get("GENERAL", "region"),
            )
            + (
                f" AS '{dwh_config.get('S3', 'log_jsonpath')}'"
                if table_name == "staging_events"
                else " AS 'auto'"
            )
        )
        conn.commit()


def insert_tables(cur: Any, conn: Any):
    for table_name, query in (pbar := tqdm(STAR_TABLES_INSERTS.items())):
        pbar.set_description(f"Inserting data into {table_name}...")
        cur.execute(query)
        conn.commit()


def main():
    # 0. Get configuration parameters
    dwh_config = process_config(Path(__file__).parents[1].joinpath("dwh.cfg"))

    # 1. Get connection and cursor
    conn, cur = get_db_connection(dwh_config)

    # 2. Load staging tables
    try:
        load_staging_tables(cur, conn, dwh_config)
    except psycopg2.Error as e:
        logging.error(f"Error loading staging tables: \n{e}")
        conn.close()
        return

    # 3. Populate star schema
    try:
        insert_tables(cur, conn)
    except psycopg2.Error as e:
        logging.error(f"Error populating star schema: \n{e}")
        conn.close()
        return

    # 4. Close connection
    conn.close()


if __name__ == "__main__":
    main()
