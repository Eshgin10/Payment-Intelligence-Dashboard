"""Integration tests use transaction-local temporary facts, never alter durable payments."""
from datetime import date
from decimal import Decimal
import os
import pytest
from fastapi.testclient import TestClient
from backend.db import connect
from backend.main import app,database,Filters
from backend import repository


@pytest.fixture
def db():
    if not os.environ.get('DATABASE_URL'): pytest.skip('DATABASE_URL required for PostgreSQL integration tests')
    with connect() as conn:
        conn.execute('CREATE TEMP TABLE payment_facts (LIKE public.payment_facts INCLUDING DEFAULTS) ON COMMIT DROP')
        conn.execute('CREATE TEMP TABLE payment_attempts (payment_id text,attempt_number int,status text) ON COMMIT DROP')
        rows=[('TEST-1',100,'successful',None,1),('TEST-2',200,'recovered',1,2),('TEST-3',300,'failed',1,2),('TEST-4',400,'pending',None,1),('TEST-5',50,'refunded',None,1)]
        for key,amount,status,reason,attempts in rows:
            conn.execute("""INSERT INTO payment_facts(payment_id,amount,amount_eur,currency,status,initial_failure_reason_id,failure_reason,
              country_code,country_name,customer_name,customer_segment,payment_method,payment_date,attempt_count,is_outlier)
              VALUES (%s,%s,%s,'EUR',%s,%s,%s,'DE','Germany','Test Customer','SMB','Card','2026-08-20 12:00+00',%s,false)""",[key,amount,amount,status,reason,'Insufficient funds' if status=='failed' else None,attempts])
            for n in range(1,attempts+1):
                attempt_status='pending' if status=='pending' else 'successful' if n==attempts and status!='failed' else 'failed'
                conn.execute('INSERT INTO payment_attempts VALUES (%s,%s,%s)',[key,n,attempt_status])
        yield conn
        conn.rollback()


@pytest.fixture
def client(db):
    app.dependency_overrides[database]=lambda:db
    with TestClient(app) as client: yield client
    app.dependency_overrides.clear()


def test_summary_uses_finalized_denominator_and_gross_settlement(db):
    result=repository.summary(db,Filters())
    assert result['total_payments']==5
    assert result['processed_volume']==Decimal('350')
    assert result['success_rate']==75
    assert result['failed_value']==300
    assert result['recovered_value']==200
    assert result['pending_payments']==1


def test_retry_value_not_double_counted(db):
    result=repository.retries(db,Filters())
    assert result[0]['recovered_value']==0
    assert result[1]['recovered_value']==200
    assert result[1]['success_rate']==50


def test_api_pagination_and_search(client):
    response=client.get('/api/payments?page_size=2&page=2')
    assert response.status_code==200
    assert response.json()['total']==5
    assert len(response.json()['items'])==2
    assert client.get('/api/payments?search=TEST-2').json()['total']==1
    assert client.get('/api/payments?search=%27%20OR%201=1--').json()['total']==0
    assert client.get('/api/payments?page_size=500').status_code==422


def test_dates_inclusive_and_zero_filled(client):
    response=client.get('/api/trends?start_date=2026-08-19&end_date=2026-08-20')
    assert response.status_code==200
    data=response.json()
    assert len(data)==2
    assert data[0]['processed_volume']==0
    assert data[1]['processed_volume']==350
    assert client.get('/api/overview?start_date=2026-09-10&end_date=2026-08-01').status_code==422


def test_filters_and_empty_denominator(client):
    response=client.get('/api/overview?country=FR').json()
    assert response['total_payments']==0
    assert response['success_rate'] is None
    assert client.get('/api/overview?status=failed').json()['failed_value']==300
    assert client.get('/api/overview?country=INVALID').status_code==422


def test_dashboard_and_breakdowns(client):
    data=client.get('/api/dashboard').json()
    assert data['overview']['success_rate']==75
    assert data['failures'][0]['failed_value']==300
    assert data['countries'][0]['payments']==5
    assert data['insights'][0]['title']=='100.0% of failed value'
    assert client.get('/api/customer-segments').json()[0]['processed_volume']==350
    assert client.get('/api/payment-methods').json()[0]['name']=='Card'


def test_no_comparison_when_baseline_absent(client):
    assert all(v is None for v in client.get('/api/overview').json()['changes'].values())


def test_unknown_payment(client):
    assert client.get('/api/payments/DOES-NOT-EXIST').status_code==404
