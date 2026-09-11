import pandas as pd
import pytest
from scripts.pipeline import generate,clean


@pytest.fixture(scope='module')
def dataset():
    return generate(1200)


def test_cleaning_preserves_audit_and_reconciles_counts(dataset):
    raw,customers=dataset
    cleaned,audit,report=clean(raw,{c[0] for c in customers})
    assert len(raw)==1400
    assert report['duplicates']==200
    assert report['invalid_records']==230
    assert len(cleaned)==970
    assert report['records_accepted']+report['records_rejected']==len(raw)
    assert cleaned.payment_id.is_unique
    assert cleaned.amount.gt(0).all()
    assert report['corrected_records']==450
    assert set(audit.action)=={'correct','reject','flag'}
    assert audit.raw_row.min()>=2


def test_negative_and_unknown_customer_are_rejected(dataset):
    raw,customers=dataset
    row=raw.iloc[[0]].copy()
    row['amount']=-1
    row['customer_id']=999999
    cleaned,audit,report=clean(row,{c[0] for c in customers})
    assert cleaned.empty
    assert report['records_rejected']==1
    assert set(audit.rule)>={'Invalid amount','Missing or unknown customer'}


def test_outliers_retained_and_currency_normalized():
    raw,customers=generate(1)
    raw['country_code']=' Germany '
    raw['currency']=''
    raw['amount']=60000
    cleaned,audit,report=clean(raw,{c[0] for c in customers})
    assert cleaned.iloc[0].currency=='EUR'
    assert cleaned.iloc[0].amount_eur==60000
    assert bool(cleaned.iloc[0].is_outlier)
    assert report['outliers']==1


def test_generator_is_reproducible():
    first,_=generate(20)
    second,_=generate(20)
    pd.testing.assert_frame_equal(first,second)
