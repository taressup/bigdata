import json
import csv
import boto3
import io

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    if not key.endswith('.json') or not key.startswith('raw/'):
        return {"status": "skipped", "reason": "Not target JSON file"}

    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8').splitlines()

    # แปลง NDJSON เป็น CSV
    output = io.StringIO()
    writer = None

    for line in content:
        try:
            row = json.loads(line)
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=row.keys())
                writer.writeheader()
            writer.writerow(row)
        except Exception as e:
            print(f"❌ Error parsing line: {e}")

    # อัปโหลดไปยัง etl/
    output.seek(0)
    output_key = 'etl/small.csv'
    s3.put_object(Bucket=bucket, Key=output_key, Body=output.getvalue())

    return {
        'statusCode': 200,
        'body': f'Successfully converted to {output_key}'
    }