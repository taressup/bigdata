import boto3
import time

athena = boto3.client('athena')
s3 = boto3.client('s3')

DATABASE = 'electronic_db'
TABLE = 'etl'
S3_OUTPUT = 's3://s3-0120-68/athena-results/'

def lambda_handler(event, context):
    query = """
    SELECT overall FROM electronic_db.etl
    WHERE overall IS NOT NULL
    ORDER BY rand() LIMIT 100
    """

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': S3_OUTPUT}
    )

    query_execution_id = response['QueryExecutionId']

    # รอผลลัพธ์
    while True:
        result = athena.get_query_execution(QueryExecutionId=query_execution_id)
        status = result['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    if status != 'SUCCEEDED':
        return {'error': f'Query failed: {status}'}

    # ดึงผลลัพธ์
    results = athena.get_query_results(QueryExecutionId=query_execution_id)
    rows = results['ResultSet']['Rows'][1:]  # ข้าม header
    values = [float(row['Data'][0]['VarCharValue']) for row in rows if 'VarCharValue' in row['Data'][0]]

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(values)
    }