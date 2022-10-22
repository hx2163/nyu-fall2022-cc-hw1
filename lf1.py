"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def validate_location(locations):
    return locations.lower() == "manhattan"
def validate_numberOfPeople(numberofpeople):
    numberofpeople = int(numberofpeople)
    return numberofpeople > 0 and numberofpeople <= 30

def validate_diningSuggestion(locations, cuisine, date, diningTime, numberOfPeople, email):
    cuisine_type = ['chinese', 'french' , 'japanese','italian','korean','american']
    if cuisine is not None and cuisine.lower() not in cuisine_type:
        return build_validation_result(False,
                                       'cuisine',
                                       'We do not have {}, would you like a different type of cuisine?  '
                                       'Our most popular cuisine are Chinese'.format(cuisine))

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'date', 'I did not understand that, what date would you like to make an appointment?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'date', 'You can book an appointment from tomorrow onwards.  What day would you like to book?')

    if diningTime is not None:
        if len(diningTime) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'diningtime', None)

        hour, minute = diningTime.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'diningtime', None)

        if hour < 10 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'diningtime', 'Our business hours are from ten a m. to ten p m. Can you specify a time during this range?')

    if locations is not None:
        if not validate_location(locations):
            return build_validation_result(False, 'locations', 'Sorry, we are only provding service in Manhattan now.')
    if numberOfPeople is not None:
        if not validate_numberOfPeople(numberOfPeople):
            return build_validation_result(False, 'numberofpeople', 'Sorry, most restaurants cannot provide service for this number of people. Could you please enter a valid number of people?')
    if email is not None:
        ses_client = boto3.client("ses", region_name="us-east-1")
        email_list = ses_client.list_verified_email_addresses()['VerifiedEmailAddresses']
        if email not in email_list:
            response = ses_client.verify_email_identity(EmailAddress = email)
            return build_validation_result(False,
                                          'emailadd',
                                          'Please valid your email address and input the email address again'
                                          )
    return build_validation_result(True, None, None)


        

""" --- Functions that control the bot's behavior --- """
def diningSuggestion(intent_request):
    cuisine = get_slots(intent_request)["cuisine"]
    date = get_slots(intent_request)["date"]
    diningTime = get_slots(intent_request)["diningtime"]
    numberOfPeople = get_slots(intent_request)["numberofpeople"]
    # phoneNumber = get_slots(intent_request)["phonenumber"]
    location = get_slots(intent_request)["locations"]
    source = intent_request['invocationSource']
    email = get_slots(intent_request)['emailadd']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_diningSuggestion(location, cuisine, date, diningTime, numberOfPeople, email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        # if cuisine is not None:
        #     output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

        return delegate(output_session_attributes, get_slots(intent_request))
    if source == 'FulfillmentCodeHook':
        print("12312312312123131313")
        sqs_client = boto3.client("sqs", region_name="us-east-1")
        queue_url = sqs_client.get_queue_url(QueueName='diningSug.fifo')['QueueUrl']
        print("test000")
        response = sqs_client.send_message(
            QueueUrl = queue_url,
            MessageAttributes={
                "locations": {
                      'DataType' : 'String',
                      'StringValue' : location
                  },
                  "cuisine": {
                      'DataType' : 'String',
                      'StringValue' : cuisine
                  },
                  "date": {
                      'DataType' : 'String',
                      'StringValue' : date
                  },
                  'diningtime':{
                    'DataType' :'String',
                    'StringValue' : diningTime

                  },
                  "numberofpeople": {
                      'DataType' : 'Number',
                      'StringValue' : numberOfPeople
                  },
                  "emailadd": {
                      'DataType' : 'String',
                      'StringValue' : email
                  }
            },
            MessageBody='string',
            MessageDeduplicationId='string',
            MessageGroupId='string'
        )
        print("test001")
        
        
        return close(intent_request['sessionAttributes'],
             'Fulfilled',
             {'contentType': 'PlainText',
              'content': 'Thanks, your order for {} has been placed and will be ready at {} for {} people'.format(email, diningTime, numberOfPeople)})
              
    # sqs_client = boto3.client('sqs')
    # sqs_url = "https://sqs.us-east-1.amazonaws.com/570223139569/dinningConfirmation"
    # msg_info = {"Cuisine" :cuisine ,"Date": date, "Time":diningTime,"Location": location,"numberOfPeople":numberOfPeople,"email":email}
    # print("message sent {}".format(msg_info))
    # try:
    #     response = sqs_client.send_message(QueueUrl = sqs_url, MessageBody = json.dumps(msg_info))
    #     print(response)
    # except ClientError as e:
    #     logging.error(e)
    #     return None

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    # return close(intent_request['sessionAttributes'],
    #              'Fulfilled',
    #              {'contentType': 'PlainText',
    #               'content': 'Thanks, your appointment at {} is booked. Have a good day!'.format(diningTime)})




""" --- Intents --- """

def greeting(intent_request):
    response = {
        "dialogAction" : {
            "type" : "Close",
            "fulfillmentState" : "Fulfilled",
            "message" : {
                "contentType" : "PlainText",
                "content" : "Hi there, how can I help?"
            }
        }
    }
    return response
def thankyou(intent_request):
    output = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        output,
        'Fulfilled',
        {
            'contentType' : 'PlainText',
            'content' : "You are welcome."
        }
    )


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greeting(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankyou(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return diningSuggestion(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.print(event['bot'])
    print("TESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTEST")
    print(event)
    print(context)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

