import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import simplejson as json
import pandas as pd
import redis
import datetime as dt
import sys

from app import app

sys.path.append('..')
from run.run import coin_a, coin_b, tri_coins, r, redis_obj


# --------------------------------
# Page Environment
# --------------------------------
root = coin_a + '-' + coin_b
refresh_rate = 1000
columns = [
    'coin',
    '{}.bid'.format(coin_b), '{}.ask'.format(coin_b), '{}.lag (s)'.format(coin_b),
    '{}.bid'.format(coin_a), '{}.ask'.format(coin_a), '{}.lag (s)'.format(coin_a),
    'Cross (buy).Option 1', root + ' (sell).Option 1', 'Prem (%).Option 1',
    'Cross (sell).Option 2', root + ' (buy).Option 2', 'Prem (%).Option 2',
    'lag (s)'
]


# --------------------------------
# Layout
# --------------------------------
layout = html.Div(
    className='row',
    children=[
        html.Div(
            className='twelve columns',
            children=[
                dash_table.DataTable(
                    id='monitor',
                    merge_duplicate_headers=True,
                    columns = [{'name': i.split('.'), 'id': i} if i not in ('coin', 'lag (s)') else {'name': ['', i], 'id': i} for i in columns],
                    style_table={'width': '100%'},
                    style_header={
                        'backgroundColor': 'rgb(50, 50, 50)'
                    },
                    style_cell={
                        'padding': '5px',
                        'margin': '0px',
                        'height': '13px',
                        'backgroundColor': 'rgb(70, 70, 70)',
                        'color': 'white'

                    },
                    style_data_conditional=[
                        {'if': {'column_id': 'Prem (%).Option 1', 'filter_query': '{Prem (%).Option 1} > 0'}, 'backgroundColor': '#007r0a'},  # #e0ece0
                        {'if': {'column_id': 'Prem (%).Option 1', 'filter_query': '{Prem (%).Option 1} < 0'}, 'backgroundColor': '#b10f00'},  # f5f0f0
                        {'if': {'column_id': 'Prem (%).Option 2', 'filter_query': '{Prem (%).Option 2} > 0'}, 'backgroundColor': '#007r0a'},
                        {'if': {'column_id': 'Prem (%).Option 2', 'filter_query': '{Prem (%).Option 2} < 0'}, 'backgroundColor': '#b10f00'},
                    ]
                ),
                dcc.Interval(
                    id='refresh',
                    interval=refresh_rate
                )
            ]
        ),
    ]
)


# --------------------------------
# Callbacks
# --------------------------------
@app.callback(
    Output('monitor', 'data'),
    [Input('refresh', 'n_intervals')]
)
def fetch_redis(n_intervals):
    t0 = dt.datetime.now()

    bbo_df = pd.DataFrame([], columns=columns)
    for coin in tri_coins + [coin_b]:
        
        if coin == coin_b:
            root_bbo = redis_obj.get(root)
            root_bbo = json.loads(root_bbo)
            root_px_bid = root_bbo[0]
            root_px_ask = root_bbo[2]
            root_ts = '{:.2f}'.format((dt.datetime.now() - dt.datetime.fromtimestamp(root_bbo[-1] / 10**9)).total_seconds())
        
        else:
            coin_dict = redis_obj.hgetall(coin_a + '-' + coin)
            coin_dict = {i: json.loads(coin_dict[i]) for i in coin_dict}

            df_dict = {}
            df_dict.update({'coin': coin})
            
            df_dict.update({coin_b + '.bid': coin_dict[coin_b][0]})
            df_dict.update({coin_b + '.ask': coin_dict[coin_b][2]})
            df_dict.update({coin_b + '.lag (s)': '{:.2f}'.format((dt.datetime.now() - dt.datetime.fromtimestamp(coin_dict[coin_b][-1] / 10**9)).total_seconds())})

            df_dict.update({coin_a + '.bid': coin_dict[coin_a][0]})
            df_dict.update({coin_a + '.ask': coin_dict[coin_a][2]})
            df_dict.update({coin_a + '.lag (s)': '{:.2f}'.format((dt.datetime.now() - dt.datetime.fromtimestamp(coin_dict[coin_a][-1] / 10**9)).total_seconds())})
            
            df_dict.update({'Cross (buy)' + '.Option 1': round(coin_dict['arb'][0], r)})
            df_dict.update({'Cross (sell)' + '.Option 2': round(coin_dict['arb'][1], r)})
            
            bbo_df = bbo_df.append(df_dict, ignore_index=True)

    bbo_df[root + ' (sell).Option 1'] = round(root_px_bid, r)
    bbo_df[root + ' (buy).Option 2'] = round(root_px_ask, r)

    bbo_df['Prem (%).Option 1'] = round(100 * (bbo_df['{} (sell).Option 1'.format(root)] - bbo_df['Cross (buy).Option 1']) / bbo_df['Cross (buy).Option 1'], 2)
    bbo_df['Prem (%).Option 2'] = round(100 * (bbo_df['Cross (sell).Option 2'] - bbo_df['{} (buy).Option 2'.format(root)]) / bbo_df['{} (buy).Option 2'.format(root)], 2)

    bbo_df['lag (s)'] = root_ts

    print('Processing Time: {}'.format((dt.datetime.now() - t0).total_seconds()))
    return bbo_df.to_dict('rows')
