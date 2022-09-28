import json
import random 
import boto3
import urllib3
import os

def lambda_handler(event, context):
    # text = event["messages"][0]["unstructured"]["text"]
    # client = boto3.client('lex-runtime')
    # response = client.post_text(botName = "chatBot",  botAlias = 'testBot1', userId = '12',inputText = text)
    return{
        'statusCode' :200,
        'headers':{
            'Access-Control-Allow-Headers':'Content-Type',
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Methods':'OPTIONS,POST,GET'
        },
        "messages":[
            {
                "type":"unstructured",
                "unstructured":{
                    "id":"1",
                    "text":"Application under development. Search functionality will be implemented in Assignment 2.",
                    "timestamp":"1"
                }
            }]
    }
    # TODO implement
    # details = get_email_info(event['EmailId'])
    # return details
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Application under development. Search functionality will be implemented in Assignment 2.')
    # }

# def get_email_info(EmailID):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('StudentDetails')
#     response = table.get_item(
#         Key = {
#             'EmailID' : EmailID
#         }
#     )
#     response_item = response.get("Item")
#     FirstName = response_item['FirstName']
#     LastName = response_item['LastName']
#     EmailID = response_item['EmailID']
#     print(response_item)
#     return response_item