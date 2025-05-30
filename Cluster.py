# import boto3
# import csv
# import io

# s3 = boto3.client('s3')
# bucket_name = 's3-0120-68'
# input_key = 'etl/small.csv'
# output_prefix = 'cluster/'

# def classify(overall):
#     try:
#         rating = float(overall)
#     except:
#         return 'other'

#     if rating > 4:
#         return 'positive'
#     elif rating <= 2:
#         return 'negative'
#     elif rating == 3:
#         return 'neutral'
#     else:
#         return 'other'

# def lambda_handler(event, context):
#     # โหลดไฟล์ CSV จาก S3
#     obj = s3.get_object(Bucket=bucket_name, Key=input_key)
#     body = obj['Body'].read().decode('utf-8')
#     lines = body.splitlines()

#     reader = csv.DictReader(lines)
    
#     output_data = {
#         'positive': [],
#         'neutral': [],
#         'negative': []
#     }

#     headers = reader.fieldnames + ['sentiment']

#     for row in reader:
#         sentiment = classify(row.get('overall'))
#         if sentiment in output_data:
#             row['sentiment'] = sentiment
#             output_data[sentiment].append(row)

#     # เขียนแต่ละกลุ่มกลับไปที่ S3
#     for sentiment, rows in output_data.items():
#         if rows:
#             buffer = io.StringIO()
#             writer = csv.DictWriter(buffer, fieldnames=headers)
#             writer.writeheader()
#             writer.writerows(rows)
#             s3.put_object(
#                 Bucket=bucket_name,
#                 Key=f"{output_prefix}{sentiment}.csv",
#                 Body=buffer.getvalue()
#             )

#     return {
#         'statusCode': 200,
#         'body': '✅ Grouped without pandas and saved to S3'
#     }


import boto3
import json
import csv
import io

s3 = boto3.client('s3')
comprehend = boto3.client('comprehend')

BUCKET = 's3-0120-68'
INPUT_KEY = 'raw/small.csv'
OUTPUT_KEY = 'etl/sentiment_result.csv'

def lambda_handler(event, context):
    # 1. Load CSV file from S3
    obj = s3.get_object(Bucket=BUCKET, Key=INPUT_KEY)
    lines = obj['Body'].read().decode('utf-8').splitlines()
    reader = csv.DictReader(lines)

    # 2. Analyze Sentiment with Comprehend
    results = []
    for row in reader:
        text = row.get('reviewText', '')  # ชื่อ column ที่มีข้อความ
        if not text.strip():
            continue

        try:
            response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
            row['predicted_sentiment'] = response['Sentiment']
            results.append(row)
        except Exception as e:
            print(f"Error analyzing: {e}")

    # 3. Write results back to S3
    if results:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

        s3.put_object(Bucket=BUCKET, Key=OUTPUT_KEY, Body=output.getvalue())
        return {'status': '✅ Sentiment analysis done!', 'output': OUTPUT_KEY}
    else:
        return {'status': '❌ No valid rows to analyze'}