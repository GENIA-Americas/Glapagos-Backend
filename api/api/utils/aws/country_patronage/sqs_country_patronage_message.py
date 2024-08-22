import boto3
import os


def send_country_patronage_request(tool_id, url, debug=False):
    if not 'SQS_COUNTRY_PATRONAGE_QUEUE' in os.environ:
        if debug:
            print('\'SQS_COUNTRY_PATRONAGE_QUEUE\' Environment not found')
        return
    queue_url = os.environ['SQS_COUNTRY_PATRONAGE_QUEUE']
    
    if queue_url == "https://sqs.{region}.amazonaws.com/{que_id}":
        if debug:
            print('\'SQS_COUNTRY_PATRONAGE_QUEUE\' Environment not found')
        return

    # Create SQS client
    sqs = boto3.client('sqs', region='us-east-2')

    

    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'tool_id': {
                'DataType': 'String',
                'StringValue': tool_id
            },
            'url': {
                'DataType': 'String',
                'StringValue': url
            },
        },
    )

    if debug:
        print(response['MessageId'])