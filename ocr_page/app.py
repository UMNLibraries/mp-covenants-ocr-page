import re
import json
# import ndjson
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

def save_doc_stats(lines, bucket, key_parts):
    num_lines = len(lines)
    num_chars = sum([len(line['Text']) for line in lines])

    stats = {
        'workflow': key_parts['workflow'],
        'remainder': key_parts['remainder'],
        'num_lines': num_lines,
        'num_chars': num_chars
    }

    out_key = f"ocr/stats/{key_parts['workflow']}/{key_parts['remainder']}.json"

    s3.put_object(
        Body=json.dumps(stats),
        Bucket=bucket,
        Key=out_key,
        StorageClass='GLACIER_IR',
        ContentType='application/json'
    )
    return out_key


def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    if 'Records' in event:
        # Get the object from a more standard put event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(
            event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    else:
        # Get the object from an EventBridge event
        bucket = event['detail']['bucket']['name']
        key = event['detail']['object']['key']

    try:
        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}})

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure it exists and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

    #Get the text blocks
    blocks=response['Blocks']

    page_info = [block for block in blocks if block['BlockType'] == 'PAGE']
    lines = [block for block in blocks if block['BlockType'] == 'LINE']
    words = [block for block in blocks if block['BlockType'] == 'WORD']

    key = key.replace('test/milwaukee', 'raw/wi-milwaukee-county')  # Temp for testing
    key_parts = re.search('(?P<status>[a-z]+)/(?P<workflow>[A-z\-]+)/(?P<remainder>.+)\.(?P<extension>[a-z]+)', key).groupdict()

    textract_json_file = save_page_ocr_json(response, bucket, key_parts)
    page_txt_file = save_page_text(lines, bucket, key_parts)
    page_stats_file = save_doc_stats(lines, bucket, key_parts)

    return {
        "statusCode": 200,
        "body": {
            "message": "hello world",
            "bucket": bucket,
            "orig": key,
            "json": textract_json_file,
            "txt": page_txt_file,
            "stats": page_stats_file
            # "location": ip.text.replace("\n", "")
        },
    }
