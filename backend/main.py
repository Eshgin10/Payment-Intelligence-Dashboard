from datetime import date
from enum import Enum
from typing import Annotated
import logging
import psycopg
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from pydantic import BaseModel, Field, model_validator
from backend.db import connect
from backend import repository as repo

app=FastAPI(title='Payment Intelligence API',version='1.0.0',description='Real PostgreSQL analytics over an explicitly synthetic payment dataset. All dates use UTC. Values are reported in EUR at fixed synthetic FX rates.')


class Status(str,Enum):
    successful='successful'
    failed='failed'
    pending='pending'
    recovered='recovered'
    refunded='refunded'


class Filters(BaseModel):
    start_date: date = date(2026,8,12)
    end_date: date = date(2026,9,10)
    country: str | None = Field(default=None,pattern=r'^[A-Z]{2}$')
    payment_method: str | None = Field(default=None,max_length=50)
    customer_segment: str | None = Field(default=None,max_length=50)
    status: Status | None = None
    failure_reason: str | None = Field(default=None,max_length=100)
    search: str | None = Field(default=None,max_length=100)

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date>self.end_date: raise ValueError('Start date must precede end date.')
        if (self.end_date-self.start_date).days>730: raise ValueError('Maximum date range is 731 days.')
        return self


FilterQuery=Annotated[Filters,Query()]


def database():
    with connect() as conn:
        # A response with multiple SQL queries observes one consistent snapshot.
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        yield conn


DB=Annotated[psycopg.Connection,Depends(database)]


@app.exception_handler(psycopg.Error)
async def db_error(request: Request,exc: psycopg.Error):
    logging.error('Database request failed: %s',type(exc).__name__)
    return JSONResponse(status_code=503,content={'detail':'The payment database is unavailable. Check the database connection and retry.'})


@app.get('/api/health')
def health(conn: DB):
    conn.execute('SELECT 1')
    return {'status':'ok','database':'postgresql'}


@app.get('/api/options')
def options(conn: DB):
    return {'countries':conn.execute('SELECT country_code AS key,country_name AS name FROM countries ORDER BY country_name').fetchall(),
      'methods':conn.execute('SELECT name FROM payment_methods ORDER BY name').fetchall(),
      'segments':['Consumer','SMB','Enterprise'],
      'dates':conn.execute('SELECT min(payment_date)::date AS start,max(payment_date)::date AS end FROM payments').fetchone()}


@app.get('/api/overview')
def overview(filters: FilterQuery,conn: DB): return repo.overview(conn,filters)


@app.get('/api/dashboard')
def dashboard(filters: FilterQuery,conn: DB):
    return {'overview':repo.overview(conn,filters),'trends':repo.trends(conn,filters),
      'countries':repo.breakdown(conn,filters,'countries'),'failures':repo.breakdown(conn,filters,'failure-reasons'),
      'retries':repo.retries(conn,filters),'insights':repo.insights(conn,filters),
      'recent':repo.payments(conn,filters.model_copy(update={'status':Status.failed}),1,5)['items']}


@app.get('/api/trends')
def trends(filters: FilterQuery,conn: DB): return repo.trends(conn,filters)


@app.get('/api/countries')
def countries(filters: FilterQuery,conn: DB): return repo.breakdown(conn,filters,'countries')


@app.get('/api/failure-reasons')
def failures(filters: FilterQuery,conn: DB): return repo.breakdown(conn,filters,'failure-reasons')


@app.get('/api/customer-segments')
def segments(filters: FilterQuery,conn: DB): return repo.breakdown(conn,filters,'customer-segments')


@app.get('/api/payment-methods')
def methods(filters: FilterQuery,conn: DB): return repo.breakdown(conn,filters,'payment-methods')


@app.get('/api/retries')
def retries(filters: FilterQuery,conn: DB): return repo.retries(conn,filters)


@app.get('/api/insights')
def insights(filters: FilterQuery,conn: DB): return repo.insights(conn,filters)


# Pagination is separate because the filter model must not consume pagination fields.
@app.get('/api/payments')
def payments(conn: DB,start_date: date=date(2026,8,12),end_date: date=date(2026,9,10),country: str|None=Query(None,pattern='^[A-Z]{2}$'),
             payment_method: str|None=Query(None,max_length=50),customer_segment: str|None=Query(None,max_length=50),
             status: Status|None=None,failure_reason: str|None=Query(None,max_length=100),search: str|None=Query(None,max_length=100),
             page: int=Query(1,ge=1,le=100000),page_size: int=Query(20,ge=1,le=100)):
    if start_date>end_date or (end_date-start_date).days>730: raise HTTPException(422,'Invalid date range; use a maximum of 731 days.')
    f=Filters(start_date=start_date,end_date=end_date,country=country,payment_method=payment_method,customer_segment=customer_segment,status=status,failure_reason=failure_reason,search=search)
    return repo.payments(conn,f,page,page_size)


@app.get('/api/payments/{payment_id}')
def payment_detail(payment_id: str,conn: DB):
    row=conn.execute('SELECT * FROM payment_facts WHERE payment_id=%s',[payment_id]).fetchone()
    if not row: raise HTTPException(404,'Payment not found.')
    row['attempts']=conn.execute('SELECT a.*,f.name AS failure_reason FROM payment_attempts a LEFT JOIN failure_reasons f USING(failure_reason_id) WHERE payment_id=%s ORDER BY attempt_number',[payment_id]).fetchall()
    return row


@app.get('/api/data-quality')
def quality(conn: DB):
    row=conn.execute('SELECT completed_at,summary FROM pipeline_runs ORDER BY run_id DESC LIMIT 1').fetchone()
    if not row: raise HTTPException(404,'Run the data pipeline to see quality results.')
    return {**row['summary'],'completed_at':row['completed_at']}


# The deployment image contains a static Next.js export. API routes remain above
# this catch-all mount so the browser can call the same origin in production.
static_dir=os.environ.get('STATIC_DIR')
if static_dir and Path(static_dir).is_dir():
    app.mount('/',StaticFiles(directory=static_dir,html=True),name='frontend')
