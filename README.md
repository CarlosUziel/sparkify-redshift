<div id="top"></div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#premise">Premise</a></li>
        <li><a href="#goal">Goal</a></li>
        <li><a href="#data">Data</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#setting-up-a-conda-environment">Setting up a conda environment</a></li>
        <li><a href="#setting-up-an-amazon-redshift-cluster">Setting up an Amazon Redshift cluster</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#additional-notes">Additional Notes</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

# Sparkify (using AWS Redshift)

A project from the [Data Engineer Nanodegree Program at Udacity](https://www.udacity.com/course/data-engineer-nanodegree--nd027) to practice data warehouses on the cloud using AWS services.

## About The Project

### Premise

> A music streaming startup, Sparkify, has grown their user base and song database and want to move their processes and data onto the cloud. Their data resides in S3, in a directory of JSON logs on user activity on the app, as well as a directory with JSON metadata on the songs in their app.
>
> As their data engineer, you are tasked with building an ETL pipeline that extracts their data from S3, stages them in Redshift, and transforms data into a set of dimensional tables for their analytics team to continue finding insights into what songs their users are listening to. You'll be able to test your database and ETL pipeline by running queries given to you by the analytics team from Sparkify and compare your results with their expected results.

<p align="right">(<a href="#top">back to top</a>)</p>

### Goal

The goal of this project is to apply what I have on data warehouses and AWS to build an ETL pipeline for a database hosted on Redshift. Data will be loaded from an S3 bucket to staging tables on Redshift. Then, data will be organized into fact and dimension tables following a star schema defined for a particular analytics focus.

<p align="right">(<a href="#top">back to top</a>)</p>

### Data

Data is stored in an S3 bucket:

- **Song data**: `s3://udacity-dend/song_data`
- **Log data**: `s3://udacity-dend/log_data`

Log data json path: `s3://udacity-dend/log_json_path.json`

#### The song dataset

A subset of real data from the [Million Song Dataset](http://millionsongdataset.com/). Each file is in JSON format and contains metadata about a song and the artist of that song. Files are located under in `s3://udacity-dend/song_data`.

For example, this is how the first file (`TRAAAAW128F429D538.json`) looks like:

```json
{
  "num_songs": 1,
  "artist_id": "ARD7TVE1187B99BFB1",
  "artist_latitude": null,
  "artist_longitude": null,
  "artist_location": "California - LA",
  "artist_name": "Casual",
  "song_id": "SOMZWCG12A8C13C480",
  "title": "I Didn't Mean To",
  "duration": 218.93179,
  "year": 0
}

```

#### Log dataset

It is composed of log files in NDJSON format generated by this [event simulator](https://github.com/Interana/eventsim) based on the songs in the dataset above. These simulate activity logs from a music streaming app based on specified configurations. Files are located under `s3://udacity-dend/log_data`.

The log files are named following a date pattern (`{year}_{month}_{day}_events.json`), and below is the first line of the first file (`2018-11-01-events`) as an example:

```json
{
  "artist": null,
  "auth": "Logged In",
  "firstName": "Walter",
  "gender": "M",
  "itemInSession": 0,
  "lastName": "Frye",
  "length": null,
  "level": "free",
  "location": "San Francisco-Oakland-Hayward, CA",
  "method": "GET",
  "page": "Home",
  "registration": 1540919166796.0,
  "sessionId": 38,
  "song": null,
  "status": 200,
  "ts": 1541105830796,
  "userAgent": "\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36\"",
  "userId": "39"
}

```

<p align="right">(<a href="#top">back to top</a>)</p>

### Data Schema

This project uses a star schema that is better visualized through an Entity Relationship Diagram (ERD). The following image shows an example ERD, as obtained with **pgadmin4** on a local PostreSQL database.

Here, *songplays* is a **fact table**, whereas *artists*, *songs*, *time* and *users* are **dimension tables**. The fact table is referencing the rest through foreign keys.

![Sparkify ERD](images/ERD.png)

<p align="right">(<a href="#top">back to top</a>)</p>

## Getting Started

To make use of this project, I recommend managing the required dependencies with Anaconda.

### Setting up a conda environment

Install miniconda:

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Install mamba:

```bash
conda install -n base -c conda-forge mamba
```

Install environment using provided file:

```bash
mamba env create -f environment.yml # alternatively use environment_core.yml if base system is not debian
mamba activate sparkify_redshift
```

### Setting up an Amazon Redshift cluster

**Create an IAM user:**

  1. IAM service is a global service, meaning newly created IAM users are not restricted to a specific region by default.
  2. Go to [AWS IAM service](https://console.aws.amazon.com/iam/home#/users) and click on the "**Add user**" button to create a new IAM user in your AWS account.
  3. Choose a name of your choice.
  4. Select "**Programmatic access**" as the access type. Click Next.
  5. Choose the **Attach existing policies directly tab**, and select the "**AdministratorAccess**". Click Next.
  6. Skip adding any tags. Click Next.
  7. Review and create the user. It will show you a pair of access key ID and secret.
  8. Take note of the pair of access key ID and secret. This pair is collectively known as Access key.

**Save access key and secret locally:**

  1. Create a new file, `_user.cfg`, and add the following:

   ```bash
   KEY= <YOUR_AWS_KEY>
   SECRET= <YOUR_AWS_SECRET>
   ```

  2. This file will be loaded internally to connect to AWS and perform various operations.
  3. **DO NOT SHARE THIS FILE WITH ANYONE!** I recommend adding this file to .gitignore to avoid accidentally pushing it to a git repository: `printf "\n_user.cfg\n" >> .gitignore`.

**Create cluster:**

  1. Fill the `dwh.cfg` configuration file. These are the basic parameters that will be used to operate on AWS. More concretely, `GENERAL` covers general parameters, `DWH` includes the necessary information to create and connect to the Redshift cluster and S3 contains information on where to find the source dataset for this project. *This file is already filled with example values*.
  2. To create the Redshift cluster, either run the `create_dwh.py` python script or follow along the notebook `notebooks/main.ipynb`.

## Usage

Project structure:

- `notebooks`: contains the main Jupyter notebook to run the project (`notebooks/main.ipynb`).
- `src`: contains the source files and scripts to build and populate the Data Warehouse.

Ensure you have set the `PYTHONPATH` environment variable as needed (e.g., `PYTHONPATH=~/sparkify_redshift/src`)

To create the Amazon Redshift cluster and populate it, either follow along the Jupyter notebook `notebooks/main.ipynb`, or run the following scripts:

```bash
python src/create_dwh.py
python src/create_tables.py
python src/etl.py
```

This can also be done from within a python instance:

```python
from create_dwh import main as run_create_dwh
from create_tables import main as run_create_tables
from etl import main as run_etl

run_create_dwh()
run_create_tables()
run_etl()
```

Helper functions to generate standard SQL queries as well as the database schema can be found in `src/sql_queries.py`.

### Example queries

To query the database, first start a connection:

```python
from utils import get_db_connection

conn, cur = get_db_connection(dwh_config)
```

**How many records are in each table?**

```python
from sql_queries import STAR_TABLES

for table_name in STAR_TABLES.keys():
    cur.execute(f"SELECT count(*) FROM {table_name}")
    print(f"{table_name} has {cur.fetchone()[0]} records.")
```

*Output:*

```bash
dim_users has 105 records.
dim_artists has 10025 records.
dim_songs has 14896 records.
dim_time has 8023 records.
fact_songplays has 1144 records.
```

**Who are the top 5 users with the highest activity?**

```python
cur.execute(
    """
    SELECT
        sub.user_id, du.first_name, du.last_name, sub.counted
    FROM
        (
            SELECT
                fs.user_id, count(*) AS counted
            FROM
                fact_songplays fs
            JOIN
                dim_users du
            ON
                fs.user_id = du.user_id
            GROUP BY
                fs.user_id
        ) sub
    JOIN
        dim_users du ON sub.user_id = du.user_id
    ORDER BY
        sub.counted DESC, user_id
    LIMIT 5
    """
)
pd.DataFrame(cur.fetchall(), columns=("user_id", "first_name", "second_name", "count"))
```

*Output:*

```bash
        user_id   first_name    second_name    count
0	    80	     Tegan	    Levine	147
1	    49	    Chloe	    Cuevas	118
2	    97	    Kate	    Harrell	84
3	    24	    Layla	    Griffin	77
4	    15	    Lily	    Koch	59
```

When done interacting with the database, close the connection:

```python
conn.close()
```

When done interacting with the Redshift cluster, delete it to avoid unnecessary charges:

```python
from utils import delete_cluster, delete_iam_roles

delete_cluster(redshift_client, dwh_config)
delete_iam_roles(iam_client, dwh_config)
```


<p align="right">(<a href="#top">back to top</a>)</p>

## Additional Notes

Source files formatted using the following commands:

```bash
isort .
autoflake -r --in-place --remove-unused-variable --remove-all-unused-imports --ignore-init-module-imports .
black .
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

## Contact

[Carlos Uziel Pérez Malla](https://www.carlosuziel-pm.dev/)

[GitHub](https://github.com/CarlosUziel) - [Google Scholar](https://scholar.google.es/citations?user=tEz_OeIAAAAJ&hl=es&oi=ao) - [LinkedIn](https://at.linkedin.com/in/carlos-uziel-p%C3%A9rez-malla-323aa5124) - [Twitter](https://twitter.com/perez_malla)

<p align="right">(<a href="#top">back to top</a>)</p>

## Acknowledgments

This README includes a summary of the official project description provided to the students of the [Data Engineer Nanodegree Program at Udacity](https://www.udacity.com/course/data-engineer-nanodegree--nd027).

Part of the contents and structure of this README was inspired by [kenhanscombe](https://github.com/kenhanscombe/project-postgres).

<p align="right">(<a href="#top">back to top</a>)</p>
