import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def create_co_mtrx(conn):
    df = query_top_10_codes(conn)
    pivot = create_pivot(df)
    co_mtrx = create_mtrx(pivot)
    return co_mtrx
    
def query_top_10_codes(conn):
    query = """
    select distinct subject_id, code
        from icd9
        where code in ('401.9', '428.0', '427.31', '518.81', '584.9', '414.01', '250.00', '599.0', '428.0', '486')
    """
    return pd.read_sql(query, conn)
    
    
def create_pivot(df):
    pivot = pd.pivot_table(df, index='subject_id', columns='code', aggfunc=len, fill_value=0)
    pivot = pd.DataFrame(pivot.to_records()).set_index('subject_id', drop=True)
    return pivot

def create_mtrx(pivot):
    co_mtrx = pivot.T.dot(pivot)
    co_mtrx = co_mtrx / pivot.sum(axis=0)
    return co_mtrx

def plot_co_mtrx(co_mtrx):
    fig, ax = plt.subplots()
    fig.set_figheight(6)
    fig.set_figwidth(10)
    sns.heatmap(co_mtrx, ax=ax)
    ax.set_ylabel('Condition 1')
    ax.set_xlabel('Condition 2')
    ax.set_title('Co-occurrence plot of top 10 ICD-9 codes in %')
    _ = ax.set_yticklabels(ax.get_xticklabels(), rotation='0')
    return fig, ax
