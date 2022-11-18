from collections import OrderedDict
from typing import Dict, Iterable, Optional

STAGING_TABLES: OrderedDict[str, Iterable[str]] = OrderedDict(
    staging_events=(
        "artist_name TEXT",
        "auth TEXT",
        "firstName TEXT",
        "gender TEXT",
        "itemInSession INT",
        "lastName TEXT",
        "length NUMERIC",
        "level TEXT",
        "location TEXT",
        "method TEXT",
        "page TEXT",
        "registration DOUBLE PRECISION",
        "sessionId INT",
        "song TEXT",
        "status INT",
        "ts BIGINT",
        "userAgent TEXT",
        "userId INT",
    ),
    staging_songs=(
        "artist_id TEXT",
        "artist_latitude DOUBLE PRECISION",
        "artist_location TEXT",
        "artist_longitude DOUBLE PRECISION",
        "artist_name TEXT",
        "duration NUMERIC",
        "num_songs INT",
        "song_id TEXT",
        "title TEXT",
        "year INT",
    ),
)
STAR_TABLES: OrderedDict[str, Iterable[str]] = OrderedDict(
    dim_users=(
        "user_id INT PRIMARY KEY",
        "first_name TEXT",
        "last_name TEXT",
        "gender TEXT",
        "level TEXT",
    ),
    dim_artists=(
        "artist_id TEXT PRIMARY KEY",
        "name TEXT NOT NULL",
        "location TEXT",
        "latitude DOUBLE PRECISION",
        "longitude DOUBLE PRECISION",
    ),
    dim_songs=(
        "song_id TEXT PRIMARY KEY",
        "title TEXT NOT NULL",
        "artist_id TEXT NOT NULL",
        "year INT",
        "duration NUMERIC NOT NULL",
    ),
    dim_time=(
        "start_time TIMESTAMP PRIMARY KEY",
        "hour INT",
        "day INT",
        "week INT",
        "month INT",
        "year INT",
        "weekday INT",
    ),
    fact_songplays=(
        "songplay_id INT IDENTITY(0, 1) PRIMARY KEY",
        "start_time TIMESTAMP NOT NULL",
        "user_id INT NOT NULL",
        "level TEXT",
        "song_id TEXT",
        "artist_id TEXT",
        "session_id INT",
        "location TEXT",
        "user_agent TEXT",
    ),
)
STAR_TABLES_CONSTRAINTS: Dict[str, Iterable[str]] = {
    "fact_songplays": (
        (
            "CONSTRAINT FK_songplays_time FOREIGN KEY(start_time) REFERENCES "
            "dim_time(start_time)"
        ),
        (
            "CONSTRAINT FK_songplays_users FOREIGN KEY(user_id) REFERENCES "
            "dim_users(user_id)"
        ),
        (
            "CONSTRAINT FK_songplays_songs FOREIGN KEY(song_id) REFERENCES "
            "dim_songs(song_id)"
        ),
        (
            "CONSTRAINT FK_songplays_artists FOREIGN KEY(artist_id) REFERENCES "
            "dim_artists(artist_id)"
        ),
    )
}
STAR_TABLES_DISTSTYLES: Dict[str, str] = {
    "fact_songplays": "DISTSTYLE EVEN",
    "dim_users": "DISTSTYLE ALL",
    "dim_artists": "DISTSTYLE ALL",
    "dim_songs": "DISTSTYLE ALL",
    "dim_time": "DISTSTYLE ALL",
}
STAR_TABLES_INSERTS: Dict[str, str] = OrderedDict(
    dim_time="""
            INSERT INTO
                dim_time (start_time, hour, day, week, month, year, weekday)
            SELECT DISTINCT
                TIMESTAMP 'epoch' + ts/1000 * interval '1 second' AS start_time,
                EXTRACT (HOUR FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS hour,
                EXTRACT (DAY FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS day,
                EXTRACT (WEEK FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS week,
                EXTRACT (MONTH FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS month,
                EXTRACT (YEAR FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS year,
                EXTRACT (DOW FROM TIMESTAMP 'epoch' + ts/1000 * interval '1 second') AS weekday
            FROM
                staging_events
            WHERE
                start_time IS NOT NULL
        """,
    dim_artists="""
            INSERT INTO
                dim_artists (artist_id, name, location, latitude, longitude)
            SELECT DISTINCT
                artist_id,
                artist_name,
                artist_location,
                artist_latitude,
                artist_longitude
            FROM
                staging_songs
            WHERE
                artist_id IS NOT NULL
        """,
    dim_songs="""
            INSERT INTO
                dim_songs (song_id, title, artist_id, year, duration)
            SELECT DISTINCT
                song_id, title, artist_id, year, duration
            FROM
                staging_songs
            WHERE
                song_id IS NOT NULL
        """,
    dim_users="""
            INSERT INTO
                dim_users (user_id, first_name, last_name, gender, level)
            SELECT DISTINCT
                userId, firstName, lastName, gender, level
            FROM
                staging_events
            WHERE
                userId IS NOT NULL
        """,
    fact_songplays="""
            INSERT INTO
                fact_songplays
                (start_time,
                user_id,
                level,
                song_id,
                artist_id,
                session_id,
                location,
                user_agent)
            SELECT DISTINCT
                TIMESTAMP 'epoch' + e.ts/1000 * interval '1 second' AS start_time,
                e.userId,
                e.level,
                s.song_id,
                s.artist_id,
                e.sessionId,
                e.location,
                e.userAgent
            FROM
                staging_events e
            JOIN
                staging_songs s
            ON
                e.song = s.title AND e.artist_name = s.name AND e.length = s.duration
            WHERE
                e.ts IS NOT NULL AND e.userId IS NOT NULL
                AND s.song_id IS NOT NULL AND e.artist_id IS NOT NULL
        """,
)


def get_drop_table_query(table_name: str) -> str:
    """Generate a DROP TABLE query given a table name.

    Args:
        table_name: table name.
    """
    return f"DROP TABLE IF EXISTS {table_name} CASCADE"


def get_create_table_query(table_name: str, table_args: Iterable[str]) -> str:
    """Generate a CREATE TABLE query given a table name and a list of arguments.

    Args:
        table_name: table name.
        table_args: An iterable of strings including column names, data types and any
            other modfiers.
    """
    return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(table_args)})"


def get_copy_s3_query(table_name: str, s3_name: str, role_arn: str, region: str):
    return (
        f"COPY {table_name} FROM '{s3_name}' CREDENTIALS 'aws_iam_role={role_arn}' "
        f"REGION '{region}' FORMAT JSON"
    )


def get_simple_select_query(
    table_name: str,
    columns: Iterable[str],
    where_columns: Optional[Dict[str, str]] = None,
    limit: Optional[int] = None,
) -> str:
    """Generate a simple select query.

    Args:
        columns: columns to select.
        table_name: table name to select columns from.
        where_columns: optionally, add a where clause. The keys and values in the
            dictionary will build an equality (i.e. WHERE key = value).
        limit: Optionally, add a query limit.

    """
    where_columns_str = (
        [f"{key} = {value}" for key, value in where_columns.items()]
        if where_columns
        else None
    )
    return (
        f"SELECT {', '.join(columns)} FROM {table_name} "
        + (f" WHERE {', '.join(where_columns_str)}" if where_columns_str else "")
        + (f" LIMIT {limit}" if limit else "")
    )
