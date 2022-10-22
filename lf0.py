import json
import random 
import boto3
import urllib3
import os
import logging
from json import dumps


def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    
    response = client.post_text(
        botName = 'DiningSuggestion',
        botAlias = 'SuggestionBot',
        userId = 'lf0',
        inputText=event['messages'][0]['unstructured']['text']
    )
    return {
        "statusCode": 200,
        'headers':{
            'Access-Control-Allow-Headers':'Content-Type',
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Methods':'OPTIONS,POST,GET'
        },
        "messages": [
          {
            "type": "unstructured",
            "unstructured": {
              "id": "string",
              "text": json.dumps(response['message'])[1:-1],
              "timestamp": "string"
            }
          }
        ],
    }

