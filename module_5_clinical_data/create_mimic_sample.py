import os, sys
import argparse
import pandas as pd
import pymysql

import mimic_queries

HOST = "35.233.174.193"
DB = 'mimic2'
USER = "jovyan"

def connect_to_mimic(host, database, user, password):
    conn = pymysql.connect(host=host,port=3306,
                       user=user,passwd=password,
                       db=database)
    return conn

def get_dataframes(conn, limit=None):
    """
    Get dataframes for ICD-9 billing data, labs, meds,
    and free texts.
    """
    names_dfs = []
    # Tuples where the first element is the name of the output excelsheet
    # and the second element is the query that we'll execute
    names_queries = [
        ('demographic', mimic_queries.demographic_query),
        ('chart_events', mimic_queries.chart_events_query),
        ('billing', mimic_queries.icd9_query),
        ('labs', mimic_queries.lab_query),
        ('meds', mimic_queries.med_query),
        ('free_text_notes', mimic_queries.text_query)
    ]
    for (name, query) in names_queries:
        names_dfs.append((name, query_mimic(query, conn, limit=limit)))
    return names_dfs

def query_mimic(query, conn, limit=None):
    """Execute a single MIMIC query with an optional limit"""
    if limit is not None:
        query += '\nlimit {0}'.format(limit)
    return pd.read_sql(query, conn)

def save_outfile(names_dataframes, outpath):
    writer = pd.ExcelWriter(outpath)
    for name, df in names_dataframes:
        df.to_excel(writer, sheet_name=name, index=None)
    writer.close()
    print("Saved {0} tables at {1}".format(len(names_dataframes), outpath))

def main():
    conn = connect_to_mimic(HOST, DB, USER, args.password)
    names_dataframes = get_dataframes(conn, args.limit)
    save_outfile(names_dataframes, args.outpath)
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help="password to mimic-ii database",
                        required=True)
    parser.add_argument('-l', '--limit', help="number of rows to limit queries",
                        type=int)
    parser.add_argument('-o', '--outpath', help="path to save excel file",
                        default='./mimic_data_samples.xlsx')
    args = parser.parse_args()
    main()
