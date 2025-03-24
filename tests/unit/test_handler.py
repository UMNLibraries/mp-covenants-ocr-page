import json
import boto3
import toml

import pytest

from ocr_page import app

with open('samconfig.toml', 'r') as f:
    config = toml.load(f)
    s3_bucket = config['default']['deploy']['parameters']['s3_bucket']
    s3_region = config['default']['deploy']['parameters']['region']

s3 = boto3.client('s3')


def build_split_step_output(bucket, region, key, page_num=1):
    """ Generates API GW Event based on output from split pages step Lambda"""

    return {
        "statusCode": 200,
        "detail": {
            "message": "hello world",
            "bucket": {
                "name": s3_bucket,
            },
            "object":  {
                "key": key,
                "page_num": page_num
            }
        }
    }


@pytest.fixture()
def no_ext_tif_event_1():
    # TIF file with .001 extension, e.g. Forsyth or Contra Costa County
    # return build_split_step_output(s3_bucket, s3_region, "raw/ca-contra-costa-county/Deeds/img1923a/19239045231500.001", 1)
    return build_split_step_output(s3_bucket, s3_region, "raw/test-county/Deeds/19499142059800.001", 1)


def test_input_output_results(no_ext_tif_event_1):
    ''' Does this run appropriately with output of mp-covenants-split-pages Lambda?'''
    fixture = no_ext_tif_event_1

    ret = app.lambda_handler(fixture, "")
    data = ret["body"]
    print(data)

    assert ret["statusCode"] == 200
    