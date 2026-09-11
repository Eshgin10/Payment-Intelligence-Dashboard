"""Deterministic synthetic data → audited cleaning → transactional PostgreSQL load."""
from __future__ import annotations

import argparse
import json
import os
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = [
    ('GB','United Kingdom','GBP',1.17), ('DE','Germany','EUR',1),
    ('FR','France','EUR',1), ('NL','Netherlands','EUR',1), ('ES','Spain','EUR',1),
    ('SE','Sweden','SEK',.089), ('LV','Latvia','EUR',1),
    ('US','United States','USD',.92), ('AU','Australia','AUD',.61), ('IE','Ireland','EUR',1),
]
METHODS = [(1,'Card'),(2,'Bank transfer'),(3,'Direct debit'),(4,'Digital wallet')]
REASONS = [(1,'Insufficient funds',True),(2,'Bank declined',True),(3,'Account closed',False),(4,'Technical failure',True),(5,'Mandate issue',False)]
PAYMENT_COLUMNS = ['payment_id','customer_id','merchant_id','payment_method_id','country_code','amount','currency','amount_eur','status','failure_reason_id','initial_failure_reason_id','attempt_count','payment_date','settled_at','is_outlier']


def generate(count: int = 50_000, seed: int = 42) -> tuple[pd.DataFrame, list[tuple]]:
    rng = random.Random(seed)
    names = ['Avery','Morgan','Alex','Sam','Jordan','Taylor','Jamie','Robin','Drew','Casey']
    surnames = ['Bennett','Martin','Weber','Laurent','Novak','Reed','Jensen','Silva','Hayes','Clarke']
    customers = []
    for i in range(1, 4001):
        country = rng.choices(COUNTRIES, [18,17,12,9,8,5,3,17,6,5])[0]
        segment = rng.choices(['Consumer','SMB','Enterprise'],[62,30,8])[0]
        customers.append((i,f'{rng.choice(names)} {rng.choice(surnames)} {i:04d}',segment,country[0],date(2023,1,1)+timedelta(days=rng.randrange(600)),rng.choices(['Low','Medium','High'],[75,20,5])[0]))
    start = date(2025,9,11)
    days = [start+timedelta(days=i) for i in range(365)]
    weights = [(0.7 if d.weekday()>4 else 1)*(1.4 if d.month==12 else 1)*(1+(d-start).days/1400) for d in days]
    rows = []
    for i in range(count):
        c = rng.choice(customers)
        co = next(x for x in COUNTRIES if x[0]==c[3])
        day = rng.choices(days,weights)[0]
        when = datetime.combine(day,datetime.min.time(),tzinfo=timezone.utc)+timedelta(seconds=rng.randrange(86400))
        method = rng.choices([1,2,3,4],[48,24,18,10])[0]
        amount_eur = round(rng.lognormvariate({'Consumer':4.2,'SMB':6.1,'Enterprise':8.3}[c[2]],.8),2)
        amount = round(amount_eur/co[3],2)
        fail_rate = {1:.13,2:.045,3:.09,4:.065}[method]
        fail_rate += .05 if co[0]=='ES' else 0
        fail_rate += .22 if co[0]=='DE' and date(2026,8,18)<=day<=date(2026,8,25) else 0
        initial = rng.random()<fail_rate
        reason = rng.choices([1,2,3,4,5],[42,28,7,17,6])[0] if initial else None
        attempts = 1
        status = 'failed' if initial else 'successful'
        if initial and reason not in [3,5] and rng.random()<.8:
            attempts = 2
            if rng.random()<.54:
                status='recovered'
            elif rng.random()<.55:
                attempts=3
                if rng.random()<.32:
                    status='recovered'
        if not initial and day>=date(2026,9,9) and rng.random()<.15:
            status='pending'
        elif status=='successful' and rng.random()<.012:
            status='refunded'
        settled = when+timedelta(hours=2+6*(attempts-1)) if status in ['successful','recovered','refunded'] else None
        rows.append(dict(zip(PAYMENT_COLUMNS,[f'PI-{i+1:07d}',c[0],rng.randrange(1,13),method,co[0],amount,co[2],round(amount*co[3],2),status,reason if status=='failed' else None,reason,attempts,when.isoformat(),settled.isoformat() if settled else '',False])))
    raw = pd.DataFrame(rows)
    # Disjoint defects: every correction and rejection remains traceable to its raw row.
    indices = rng.sample(range(count),min(count,950))
    for i in indices[:150]: raw.loc[i,'country_code']=' '+next(c[1] for c in COUNTRIES if c[0]==raw.loc[i,'country_code'])+' '
    for i in indices[150:300]: raw.loc[i,'status']=raw.loc[i,'status'].upper()
    for i in indices[300:400]: raw.loc[i,'payment_date']=datetime.fromisoformat(raw.loc[i,'payment_date']).strftime('%Y/%m/%d %H:%M:%S+00:00')
    for i in indices[400:500]: raw.loc[i,'customer_id']=None
    for i in indices[500:550]: raw.loc[i,'amount']=-abs(raw.loc[i,'amount'])
    raw['amount']=raw['amount'].astype(object)
    for i in indices[550:580]: raw.loc[i,'amount']='not-an-amount'
    for i in indices[580:630]: raw.loc[i,'currency']=''
    for i in indices[630:700]: raw.loc[i,'amount']=float(raw.loc[i,'amount'])*100
    for i in indices[700:750]: raw.loc[i,'payment_date']='impossible-date'
    raw = pd.concat([raw,raw.iloc[indices[750:950]].copy()],ignore_index=True)
    return raw, customers


def clean(raw: pd.DataFrame, customer_ids: set[int]) -> tuple[pd.DataFrame,pd.DataFrame,dict]:
    frame = raw.copy().reset_index(drop=True)
    audit: list[dict] = []
    def record(mask: pd.Series, rule: str, action: str):
        for idx in frame.index[mask]:
            audit.append({'raw_row':int(idx)+2,'payment_id':str(frame.loc[idx,'payment_id']),'rule':rule,'action':action})
    duplicates = frame.duplicated('payment_id',keep='first')
    record(duplicates,'Duplicate payment ID','reject')
    missing = frame[['customer_id','amount','payment_date','currency']].isna().any(axis=1) | frame['currency'].eq('')
    missing_count = int(missing.sum())
    frame = frame.loc[~duplicates].copy()
    names = {x[1].lower():x[0] for x in COUNTRIES}
    normalized = frame.country_code.astype(str).str.strip().str.lower().map(lambda x:names.get(x,x.upper()))
    record(frame.country_code.ne(normalized),'Country normalization','correct')
    frame['country_code']=normalized
    status = frame.status.astype(str).str.strip().str.lower()
    record(frame.status.ne(status),'Status casing','correct')
    frame['status']=status
    curr = frame.country_code.map({x[0]:x[2] for x in COUNTRIES})
    missing_currency = frame.currency.isna() | frame.currency.eq('')
    record(missing_currency & curr.notna(),'Currency inferred from country','correct')
    frame.loc[missing_currency,'currency']=curr[missing_currency]
    frame['amount']=pd.to_numeric(frame.amount,errors='coerce')
    frame['customer_id']=pd.to_numeric(frame.customer_id,errors='coerce')
    parsed = pd.to_datetime(frame.payment_date,format='mixed',errors='coerce',utc=True)
    record(frame.payment_date.astype(str).str.contains('/',regex=False) & parsed.notna(),'Date format normalization','correct')
    frame['payment_date']=parsed
    frame['settled_at']=pd.to_datetime(frame.settled_at,format='mixed',errors='coerce',utc=True)
    invalid_customer = ~frame.customer_id.isin(customer_ids)
    invalid_amount = frame.amount.isna() | frame.amount.le(0)
    invalid_date = frame.payment_date.isna()
    invalid_country = ~frame.country_code.isin([x[0] for x in COUNTRIES]) | frame.currency.ne(curr)
    invalid_status = ~frame.status.isin(['successful','failed','pending','recovered','refunded'])
    settled_status = frame.status.isin(['successful','recovered','refunded'])
    invalid_settlement = settled_status.ne(frame.settled_at.notna()) | frame.settled_at.lt(frame.payment_date)
    invalid = invalid_customer | invalid_amount | invalid_date | invalid_country | invalid_status | invalid_settlement
    for mask,rule in [(invalid_customer,'Missing or unknown customer'),(invalid_amount,'Invalid amount'),(invalid_date,'Invalid payment date'),(invalid_country,'Country or currency invalid'),(invalid_status,'Invalid status'),(invalid_settlement,'Invalid settlement')]:
        record(mask,rule,'reject')
    accepted = frame.loc[~invalid].copy()
    rate = accepted.country_code.map({x[0]:x[3] for x in COUNTRIES})
    accepted['amount_eur']=(accepted.amount*rate).round(2)
    accepted['is_outlier']=accepted.amount_eur.gt(50_000)
    for idx in accepted.index[accepted.is_outlier]:
        audit.append({'raw_row':int(idx)+2,'payment_id':str(accepted.loc[idx,'payment_id']),'rule':'EUR value above 50,000; retained for review','action':'flag'})
    report = pd.DataFrame(audit,columns=['raw_row','payment_id','rule','action'])
    corrected_rows = report.loc[report.action.eq('correct'),'raw_row'].nunique()
    summary = {
        'records_processed':len(raw),'duplicates':int(duplicates.sum()),'missing_fields':missing_count,
        'invalid_records':int(invalid.sum()),'records_rejected':len(raw)-len(accepted),
        'records_accepted':len(accepted),'outliers':int(accepted.is_outlier.sum()),
        'corrected_records':int(corrected_rows),'data_health':round(100*len(accepted)/len(raw),2),
        'seed':42,'dataset_start':'2025-09-11','dataset_end':'2026-09-10',
        'checks':[{'name':rule,'action':action,'affected_records':int(len(g))} for (rule,action),g in report.groupby(['rule','action'])],
    }
    assert accepted.payment_id.is_unique
    assert accepted.amount.gt(0).all()
    return accepted,report,summary


def python_value(value):
    if pd.isna(value): return None
    if isinstance(value,pd.Timestamp): return value.to_pydatetime()
    if hasattr(value,'item'): return value.item()
    return value


def load(cleaned: pd.DataFrame, customers: list[tuple], summary: dict):
    load_dotenv(ROOT/'.env')
    url = os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('Set DATABASE_URL in .env before loading PostgreSQL.')
    with psycopg.connect(url) as conn:
        conn.execute((ROOT/'sql/schema.sql').read_text())
        if conn.execute('SELECT count(*) FROM payments').fetchone()[0]:
            raise RuntimeError('Database already contains payments. Use a fresh database; the loader never erases existing data.')
        with conn.cursor() as cur:
            cur.executemany('INSERT INTO countries VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',COUNTRIES)
            cur.executemany('INSERT INTO payment_methods VALUES (%s,%s) ON CONFLICT DO NOTHING',METHODS)
            cur.executemany('INSERT INTO failure_reasons VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',REASONS)
            cur.executemany('INSERT INTO merchants VALUES (%s,%s) ON CONFLICT DO NOTHING',[(i,n) for i,n in enumerate(['Northstar Commerce','Forma Studio','Atlas Software','Common Goods','Orbit Travel','Field Supply','Linear Media','Evergreen Energy','Craft Market','Studio Health','Cove Retail','Alto Services'],1)])
            cur.executemany('INSERT INTO customers(customer_id,customer_name,customer_segment,country_code,signup_date,risk_level) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',customers)
            with cur.copy(f"COPY payments ({','.join(PAYMENT_COLUMNS)}) FROM STDIN") as copy:
                for row in cleaned[PAYMENT_COLUMNS].itertuples(index=False,name=None):
                    values = [python_value(x) for x in row]
                    for i in [1,2,3,9,10,11]:
                        if values[i] is not None: values[i]=int(values[i])
                    copy.write_row(values)
            with cur.copy('COPY payment_attempts(payment_id,attempt_number,attempt_date,status,failure_reason_id,processor_response) FROM STDIN') as copy:
                for row in cleaned.itertuples(index=False):
                    for n in range(1,int(row.attempt_count)+1):
                        status = 'pending' if row.status=='pending' else ('successful' if n==row.attempt_count and row.status!='failed' else 'failed')
                        failure = int(row.initial_failure_reason_id) if status=='failed' else None
                        copy.write_row((row.payment_id,n,row.payment_date.to_pydatetime()+timedelta(hours=6*(n-1)),status,failure,{'successful':'00 · Approved','pending':'09 · Processing','failed':'05 · Declined'}[status]))
        conn.execute((ROOT/'sql/views.sql').read_text())
        checks = conn.execute((ROOT/'sql/data_quality.sql').read_text()).fetchall()
        if any(v for _,v in checks): raise ValueError(f'Post-load validation failed: {checks}')
        summary['database_checks']=[{'name':name,'violations':n} for name,n in checks]
        conn.execute('INSERT INTO pipeline_runs(summary) VALUES (%s)',[Jsonb(summary)])
    # The context manager commits the entire load only after all checks pass.


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--load',action='store_true')
    args=parser.parse_args()
    raw,customers=generate()
    (ROOT/'data/raw').mkdir(parents=True,exist_ok=True)
    (ROOT/'data/clean').mkdir(parents=True,exist_ok=True)
    raw.to_csv(ROOT/'data/raw/payments.csv',index=False)
    cleaned,audit,summary=clean(pd.read_csv(ROOT/'data/raw/payments.csv'),{c[0] for c in customers})
    cleaned.to_csv(ROOT/'data/clean/payments.csv',index=False)
    audit.to_csv(ROOT/'data/clean/audit.csv',index=False)
    if args.load: load(cleaned,customers,summary)
    (ROOT/'data/clean/quality-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
