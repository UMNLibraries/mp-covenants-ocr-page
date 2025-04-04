import re
import time
import json
import uuid
import urllib.parse
import boto3

'''
Folder structure:

covenants-deeds-images
    -raw
        -mn-ramsey-county
        -wi-milwaukee-county
    -ocr
        -txt
            -mn-ramsey-county
            -wi-milwaukee-county
        -json
            -mn-ramsey-county
            -wi-milwaukee-county
        -stats
            -mn-ramsey-county
            -wi-milwaukee-county
        -hits
            -mn-ramsey-county
            -wi-milwaukee-county
    -web
        -mn-ramsey-county
        -wi-milwaukee-county
'''

s3 = boto3.client('s3')
textract = boto3.client('textract')

def save_page_ocr_json(textract_response, bucket, key_parts):
    out_key = f"ocr/json/{key_parts['workflow']}/{key_parts['remainder']}.json"

    s3.put_object(
        Body=json.dumps(textract_response),
        Bucket=bucket,
        Key=out_key,
        StorageClass='GLACIER_IR',
        ContentType='application/json'
    )
    return out_key

def save_page_text(lines, bucket, key_parts):
    text_blob = '\n'.join([line['Text'] for line in lines])

    out_key = f"ocr/txt/{key_parts['workflow']}/{key_parts['remainder']}.txt"

    # Upload raw text to destination bucket/key
    s3.put_object(
        Body=text_blob,
        Bucket=bucket,
        Key=out_key,
        StorageClass='GLACIER_IR',
        ContentType='text/plain'
    )
    return out_key

def save_doc_stats(lines, bucket, key_parts, handwriting_pct, public_uuid):
    num_lines = len(lines)
    num_chars = sum([len(line['Text']) for line in lines])

    stats = {
        'workflow': key_parts['workflow'],
        'remainder': key_parts['remainder'],
        'public_uuid': public_uuid,
        'num_lines': num_lines,
        'num_chars': num_chars,
        'handwriting_pct': handwriting_pct
    }

    out_key = f"ocr/stats/{key_parts['workflow']}/{key_parts['remainder']}__{public_uuid}.json"

    s3.put_object(
        Body=json.dumps(stats),
        Bucket=bucket,
        Key=out_key,
        StorageClass='GLACIER_IR',
        ContentType='application/json'
    )
    return out_key


def lambda_handler(event, context):
    """This Lambda function receives a link to an s3 image key and runs Textract's detect_document_text method to create creates 3 new files: a Textract JSON file, a simple TXT file containing a text blob of all text found, and a stats json, which contains basic statistics like the amount of the page that is estimated to be handwritten, the number of lines, and number of words. Output of this function is sent to a parallel step that will use the OCRed text to search for racial covenant terms, and another that will create a web-friendly version of the image."""

    if 'Records' in event:
        # Get the object from a more standard put event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(
            event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    elif 'key' in event:
        # Probably coming from "map" state of step function, a result of mp-covenants-split-pages
        bucket = event['bucket']
        key = event['key']
    else:
        # Get the object from an EventBridge event
        bucket = event['detail']['bucket']['name']
        key = event['detail']['object']['key']

    # Pause n seconds * splitpage num if this is a splitpage to avoid throughput issues on textract
    splitpage_match = re.search(r'_SPLITPAGE_(\d+)\.', key)
    if splitpage_match:
        splitpage_num = int(splitpage_match.group(1))
        delay = 0.3 * splitpage_num
        print(f"Splitpage {splitpage_num}: Sleeping for {delay} seconds...")
        time.sleep(delay)

    try:
        print(bucket, key)
        # Actual OCR invocation. This is a synchronous operation.
        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}})

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure it exists and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

    # Get the text blocks
    blocks=response['Blocks']

    page_info = [block for block in blocks if block['BlockType'] == 'PAGE']
    lines = [block for block in blocks if block['BlockType'] == 'LINE']
    words = [block for block in blocks if block['BlockType'] == 'WORD']

    # How much of this page is handwritten?
    handwriting_words = [word for word in words if word["TextType"] == 'HANDWRITING']
    if len(words) > 0:
        handwriting_pct = round(len(handwriting_words) / len(words), 2)
    else:
        handwriting_pct = 0

    # key = key.replace('test/milwaukee', 'raw/wi-milwaukee-county')  # Temp for testing
    key_parts = re.search(r'(?P<status>[a-z]+)/(?P<workflow>[A-z\-]+)/(?P<remainder>.+)\.(?P<extension>[A-z\d]+)', key).groupdict()

    # Doing this here because the following steps all need to know this UUID, which is random, and is appended to web-friendly file name to deter scraping of public images.
    public_uuid = uuid.uuid4().hex

    textract_json_file = save_page_ocr_json(response, bucket, key_parts)
    page_txt_file = save_page_text(lines, bucket, key_parts)
    page_stats_file = save_doc_stats(lines, bucket, key_parts, handwriting_pct, public_uuid)

    return {
        "statusCode": 200,
        "body": {
            "message": "hello world",
            "bucket": bucket,
            "orig": key,
            "json": textract_json_file,
            "txt": page_txt_file,
            "stats": page_stats_file,
            "uuid": public_uuid,
            "handwriting_pct": handwriting_pct
        },
    }
