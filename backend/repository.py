"""Parameterized SQL. Frontend receives bounded aggregates, never the full dataset."""
from datetime import timedelta
from psycopg import sql

SETTLED="status IN ('successful','recovered','refunded')"


def scope(filters):
    clauses=['payment_date >= %(start_date)s::date','payment_date < (%(end_date)s::date + 1)']
    params=filters.model_dump()
    for key in ['country','payment_method','customer_segment','status','failure_reason']:
        if params.get(key):
            column='country_code' if key=='country' else key
            clauses.append(f'{column} = %({key})s')
    if params.get('search'):
        params['search']='%'+params['search'].replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        clauses.append('(payment_id ILIKE %(search)s OR customer_name ILIKE %(search)s)')
    return ' AND '.join(clauses),params


def summary(conn,filters):
    where,params=scope(filters)
    return conn.execute(f"""SELECT count(*) AS total_payments,
      count(*) FILTER (WHERE status='pending') AS pending_payments,
      count(*) FILTER (WHERE status<>'pending') AS finalized_payments,
      coalesce(sum(amount_eur) FILTER (WHERE {SETTLED}),0) AS processed_volume,
      100.0*count(*) FILTER (WHERE {SETTLED})/nullif(count(*) FILTER (WHERE status<>'pending'),0) AS success_rate,
      coalesce(sum(amount_eur) FILTER (WHERE status='failed'),0) AS failed_value,
      coalesce(sum(amount_eur) FILTER (WHERE status='recovered'),0) AS recovered_value,
      count(*) FILTER (WHERE status='recovered') AS recovered_payments,
      count(*) FILTER (WHERE initial_failure_reason_id IS NOT NULL) AS initially_failed,
      coalesce(sum(amount_eur) FILTER (WHERE status='refunded'),0) AS refunded_value
      FROM payment_facts WHERE {where}""",params).fetchone()


def overview(conn,filters):
    current=summary(conn,filters)
    days=(filters.end_date-filters.start_date).days+1
    previous=summary(conn,filters.model_copy(update={'end_date':filters.start_date-timedelta(days=1),'start_date':filters.start_date-timedelta(days=days)}))
    changes={}
    for key in ['processed_volume','success_rate','failed_value','recovered_value']:
        old,new=previous[key],current[key]
        changes[key]=None if old is None or new is None or old==0 else float(new-old) if key=='success_rate' else float((new-old)/old*100)
    return {**current,'changes':changes,'previous':previous,'period':{'start':filters.start_date,'end':filters.end_date}}


def trends(conn,filters):
    where,params=scope(filters)
    return conn.execute(f"""WITH daily AS (
      SELECT (payment_date AT TIME ZONE 'UTC')::date AS day,
      coalesce(sum(amount_eur) FILTER (WHERE {SETTLED}),0) AS processed_volume,
      coalesce(sum(amount_eur) FILTER (WHERE status='failed'),0) AS failed_value,
      count(*) AS payments FROM payment_facts WHERE {where} GROUP BY 1)
      SELECT d.day::date AS day,coalesce(processed_volume,0) AS processed_volume,
      coalesce(failed_value,0) AS failed_value,coalesce(payments,0) AS payments
      FROM generate_series(%(start_date)s::date,%(end_date)s::date,'1 day') d(day)
      LEFT JOIN daily ON daily.day=d.day ORDER BY d.day""",params).fetchall()


def breakdown(conn,filters,dimension):
    columns={'countries':('country_code','country_name'),'failure-reasons':('failure_reason','failure_reason'),
             'customer-segments':('customer_segment','customer_segment'),'payment-methods':('payment_method','payment_method')}
    key,label=columns[dimension]
    where,params=scope(filters)
    if dimension=='failure-reasons': where+=" AND status='failed'"
    return conn.execute(f"""SELECT {key} AS key,{label} AS name,count(*) AS payments,
      coalesce(sum(amount_eur) FILTER (WHERE {SETTLED}),0) AS processed_volume,
      coalesce(sum(amount_eur) FILTER (WHERE status='failed'),0) AS failed_value,
      100.0*count(*) FILTER (WHERE {SETTLED})/nullif(count(*) FILTER (WHERE status<>'pending'),0) AS success_rate
      FROM payment_facts WHERE {where} GROUP BY {key},{label} ORDER BY failed_value DESC, name""",params).fetchall()


def retries(conn,filters):
    where,params=scope(filters)
    return conn.execute(f"""WITH selected AS (SELECT * FROM payment_facts WHERE {where})
      SELECT a.attempt_number,count(*) AS attempts,count(*) FILTER (WHERE a.status='successful') AS successes,
      100.0*count(*) FILTER (WHERE a.status='successful')/nullif(count(*),0) AS success_rate,
      coalesce(sum(p.amount_eur) FILTER (WHERE a.status='successful' AND a.attempt_number>1),0) AS recovered_value
      FROM selected p JOIN payment_attempts a USING(payment_id) GROUP BY 1 ORDER BY 1""",params).fetchall()


def insights(conn,filters):
    result=[]
    total=summary(conn,filters)
    countries=breakdown(conn,filters,'countries')
    failures=breakdown(conn,filters,'failure-reasons')
    if failures and total['failed_value']:
        top=failures[0]
        share=round(float(top['failed_value']/total['failed_value']*100),1)
        result.append({'title':f"{share}% of failed value",'body':f"{top['name']} is the largest source of unrecovered payment value.",'filter':{'failure_reason':top['name'],'status':'failed'},'tag':'Failure driver'})
    eligible=[c for c in countries if c['success_rate'] is not None and c['payments']>=30]
    if eligible:
        worst=min(eligible,key=lambda c:c['success_rate'])
        result.append({'title':f"{worst['name']} · {float(worst['success_rate']):.1f}%",'body':'Lowest final success rate among markets with at least 30 payments in this period.','filter':{'country':worst['key']},'tag':'Market to review'})
    if total['initially_failed']:
        rate=100*total['recovered_payments']/total['initially_failed']
        result.append({'title':f"{rate:.1f}% recovered",'body':f"Retries recovered {total['recovered_payments']:,} of {total['initially_failed']:,} initially failed payments.",'filter':{'status':'recovered'},'tag':'Retry impact'})
    return result[:3]


def payments(conn,filters,page,page_size):
    where,params=scope(filters)
    total=conn.execute(f'SELECT count(*) AS n FROM payment_facts WHERE {where}',params).fetchone()['n']
    params.update(limit=page_size,offset=(page-1)*page_size)
    rows=conn.execute(f"""SELECT payment_id,customer_name,country_code,amount,currency,amount_eur,
      payment_method,status,attempt_count,payment_date,is_outlier FROM payment_facts WHERE {where}
      ORDER BY payment_date DESC,payment_id LIMIT %(limit)s OFFSET %(offset)s""",params).fetchall()
    return {'items':rows,'total':total,'page':page,'page_size':page_size}
