import json
import boto3
import requests


def sendses(emailadd, message):
    
    SENDER = "djd28176@gmail.com" 
    RECIPIENT = emailadd 
    print(message)
    
    AWS_REGION = "us-east-1"
    
    
    SUBJECT = "Hey This is your restaurant suggestions!!"

    # The email body for recipients with non-HTML email clients.

    BODY_TEXT = message
                
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Hey This is your restaurant suggestions: </h1>
        """+ message+ """
    </body>
    </html>"""            

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name='us-east-1')
    
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
        
                        'Data': BODY_HTML
                    },
                    'Text': {
        
                        'Data': BODY_TEXT
                    },
                },
                'Subject': {

                    'Data': SUBJECT
                },
            },
            Source=SENDER
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        
        
        
def search(cuisine):
    payload = {
        "query": {
            "match":{
                "Cuisine" : str(cuisine)
            }
        }
    }
    url = 'esendpointurl'
    data = requests.get(url, auth = ('username', 'password'), json=payload).json()#.content.decode()
    #data = es.search(index="restaurants", body={"query": {"match": {'Cuisine':cuisine}}})
    print("search complete", data.get('hits').get('hits'))#['hits']['hits'])
    return data['hits']['hits']



def get_restaurant_data(ids):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')
    ans = '<p> Hi! Here are our recommendations: </p>'
    i = 1
    
    for id in ids:
        if i<=3:
            response = table.get_item(
                Key={
                    'id': id
                }
            )
            print(response)
            response_item = response.get("Item")
            print(response_item)
            restaurant_name = response_item['name']
            restaurant_address = response_item['address']
            restaurant_phoneNumber = response_item['phone_number']
            restaurant_rating = response_item['rating']
            ans += "<p>{}. {}, with {} stars, located at {}, you can contact them with phone number: {} </p>".format(i, restaurant_name, restaurant_rating, restaurant_address,restaurant_phoneNumber)
            # return ans
            i += 1
        else:
            break
    
    print(ans)
    return ans 
    


def lambda_handler(event, context):
    
    print(event)
    message = event['Records'][0]['messageAttributes']
    print("check")
    print(message)
    
    
    
    try:
        
        location = message['locations']['stringValue']
        cuisine = message['cuisine']['stringValue']
        dining_date = message['date']['stringValue']
        dining_time = message['diningtime']['stringValue']
        num_people = message['numberofpeople']['stringValue']
        email = message['emailadd']['stringValue']
        print(location, cuisine, dining_date, dining_time, num_people, email)
        
        
        ids = search(cuisine)
        ids = list(map(lambda x: x['_source']['ID'], ids))
        print("check ID")
        print(ids)
        rest_details = get_restaurant_data(ids)
        
        sendses(email, rest_details)
        # message.delete()
    except Exception as e:
        print(e)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda LF2!')
    }
