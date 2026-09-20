"""한국 시간 기준, 날짜 양 끝 포함. 무기록일/월도 평균 분모에 포함한다."""
import pandas as pd
from lib import db


def summarize(conn,start,end):
    if start>end: raise ValueError('시작일은 종료일보다 늦을 수 없습니다.')
    dates=pd.date_range(start,end,freq='D')
    daily=pd.DataFrame(0.0,index=dates,columns=['pages','minutes','finishes'])
    rows=db.all_activities(conn)
    if not rows.empty:
        rows['day']=pd.to_datetime(rows['date'],unit='s',utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None).dt.normalize()
        rows=rows[(rows['day']>=pd.Timestamp(start)) & (rows['day']<=pd.Timestamp(end))]
        progress=rows[rows['kind']==4].copy()
        progress['pages']=pd.to_numeric(progress['pages_read'],errors='coerce').fillna(0).clip(lower=0)
        seconds=pd.to_numeric(progress['seconds_read'],errors='coerce')
        progress['minutes']=(seconds/60).fillna(pd.to_numeric(progress['minutes_read'],errors='coerce')).fillna(0).clip(lower=0)
        if not progress.empty:
            daily[['pages','minutes']]=progress.groupby('day')[['pages','minutes']].sum().reindex(dates,fill_value=0)
        completed=rows[(rows['event_type']=='completed') | ((rows['kind']==5)&rows['event_type'].isna())]
        if not completed.empty: daily['finishes']=completed.groupby('day').size().reindex(dates,fill_value=0)
    monthly=daily.resample('MS').sum()
    totals=daily.sum()
    return {'daily':daily,'monthly':monthly,'days':len(dates),'months':len(monthly),
            'pages':float(totals['pages']),'minutes':float(totals['minutes']),'finishes':int(totals['finishes']),
            'pages_per_day':float(totals['pages'])/len(dates),'minutes_per_day':float(totals['minutes'])/len(dates),
            'books_per_month':float(totals['finishes'])/len(monthly)}
