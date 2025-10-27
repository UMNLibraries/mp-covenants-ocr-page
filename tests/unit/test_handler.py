import json
import boto3
import toml

import pytest

from ocr_page import app

with open('samconfig.toml', 'r') as f:
    config = toml.load(f)
    s3_bucket_in = config['default']['deploy']['parameters']['s3_bucket_in']
    s3_bucket_out = config['default']['deploy']['parameters']['s3_bucket_out']
    s3_bucket = config['default']['deploy']['parameters']['s3_bucket']
    s3_region = config['default']['deploy']['parameters']['region']

s3 = boto3.client('s3')


def build_split_step_output(s3_bucket, out_bucket, region, key, page_num=1):
    """ Generates API GW Event based on output from split pages step Lambda"""
    """ If out_bucket not set, assumes input and output coming from same bucket"""

    event_json = {
        "statusCode": 200,
        "detail": {
            "message": "hello world",
            "bucket": {
                "name": s3_bucket,
            },
            "object":  {
                "key": key,
                "page_num": page_num,
                "in_bucket": s3_bucket,
                "out_bucket": out_bucket,
            }
        }
    }

    if out_bucket:
        event_json['detail']['object']['in_bucket'] = s3_bucket
        event_json['detail']['object']['out_bucket'] = out_bucket

    return event_json


@pytest.fixture()
def no_ext_tif_event_1():
    # TIF file with .001 extension, e.g. Forsyth or Contra Costa County
    # return build_split_step_output(s3_bucket, s3_region, "raw/ca-contra-costa-county/Deeds/img1923a/19239045231500.001", 1)
    return build_split_step_output(s3_bucket, None, s3_region, "raw/test-county/Deeds/19499142059800.001", 1)


@pytest.fixture()
def stearns_2_bucket_event_1():
    return build_split_step_output(s3_bucket_in, s3_bucket_out, s3_region, "test/mn-stearns-county/mn_stearns-usmnstr-ftl-idx-0001-0000-0000-000_00001-000.jpg", 1)


@pytest.fixture()
def stearns_2_bucket_event_2():
    return build_split_step_output(s3_bucket_in, s3_bucket_out, s3_region, "test/mn-stearns-county/mn_stearns-usmnstr-dee-346-000-0000-000_00006-000.jpg", 1)


def test_input_output_results(no_ext_tif_event_1):
    ''' Does this run appropriately with output of mp-covenants-split-pages Lambda?'''
    fixture = no_ext_tif_event_1

    ret = app.lambda_handler(fixture, "")
    data = ret["body"]
    print(data)

    assert ret["statusCode"] == 200


def test_input_output_results_out_bucket(stearns_2_bucket_event_1):
    ''' Does this run appropriately with output of mp-covenants-split-pages Lambda?'''
    fixture = stearns_2_bucket_event_1

    ret = app.lambda_handler(fixture, "")
    data = ret["body"]
    print(data)

    assert ret["statusCode"] == 200
    assert data["bucket"] == None
    assert s3_bucket_in is not None
    assert data["in_bucket"] == s3_bucket_in
    assert data["out_bucket"] == s3_bucket_out


def test_input_output_results_out_bucket(stearns_2_bucket_event_2):
    ''' Does this run appropriately with output of mp-covenants-split-pages Lambda?'''
    fixture = stearns_2_bucket_event_2

    ret = app.lambda_handler(fixture, "")
    data = ret["body"]
    print(data)

    assert ret["statusCode"] == 200
    assert data["bucket"] == None
    assert s3_bucket_in is not None
    assert data["in_bucket"] == s3_bucket_in
    assert data["out_bucket"] == s3_bucket_out