"""
Simple Python Lambda service providing example for a small business "voice site". You know,
this is like the Alexa version of your web site.

Intents supported:
  Amazon.HelpIntent
  Activity
  Alerts

"""

import logging
import re
import feedparser
from html.parser import HTMLParser

logger = logging.getLogger()
logger.setLevel(logging.INFO)

alerts = feedparser.parse('https://www.us-cert.gov/ncas/alerts.xml')
activity = feedparser.parse('https://www.us-cert.gov/ncas/current-activity.xml')

class AlertHTMLParser(HTMLParser):

    overview = False

    alerts_text = ''

    def handle_starttag(self,tag,attrs):
        if self.overview and tag != 'p'and tag != 'br':
            self.overview = False
    
    def handle_data(self,data):
        if data == 'Overview':
            self.overview = True
        elif len(data) > 20 and self.overview:
            self.alerts_text += re.sub('<[^>]*>','',data) + "<break time='650ms'/>"

alert_parser = AlertHTMLParser()

for entry in alerts['entries'][0:3]:
    alert_parser.alerts_text += entry['title']
    alert_parser.feed(entry['summary'])

class ActHTMLParser(HTMLParser):

    summary = True

    act_text = ''

    def handle_data(self,data):
        if len(data) > 100 and self.summary:
            self.act_text += re.sub('<[^>]*>','',data) + "<break time='650ms'/>"
            self.summary = False

act_parser = ActHTMLParser()

for entry in activity['entries'][0:3]:
    act_parser.act_text += entry['title']
    act_parser.feed(entry['summary'])

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):

    card_output = re.sub('<[^>]*>','',output)
    
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title': 'Internet Threats',
            'content': card_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Your functions to implement your intents ------------------

def activity(intent, session):
    session_attributes = {}
    reprompt_text = None
    speech_output = ""
    should_end_session = True

    speech_output = "<speak>" + re.sub('<[^>]*','',act_parser.act_text) + "</speak>"

    return build_response(session_attributes, build_speechlet_response
                          (intent['name'], speech_output, reprompt_text, should_end_session))

def alerts(intent, session):
    session_attributes = {}
    reprompt_text = None
    speech_output = ""
    should_end_session = True

    speech_output = "<speak>" + re.sub('<[^>]*','',alert_parser.alerts_text) +"</speak>"

    return build_response(session_attributes, build_speechlet_response
                          (intent['name'], speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "<speak>Thank you for keeping up to date with the latest Internet threats. " \
      "Have a nice day! </speak>"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))




# --------------- Primary Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    logger.info("on_session_started requestId=" + session_started_request['requestId'] +
                ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    logger.info("on_launch requestId=" + launch_request['requestId'] +
                ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return build_response({},build_speechlet_response(
        "Internet Threats", "<speak>Welcome to Internet Threats. This skill grabs the latest activity and alerts from the U S Computer Emergency Response Team.</speak>","",False))


def get_help():
    """ Called when the user asks for help
    """

    return build_response({},build_speechlet_response(
        "Tech Em Studios","""<speak>Internet Threats grabs the latest activity and alerts from the U S Computer Emergency Response Team. Just ask Internet Threats for Activity or Alerts.</speak>""","",False)) 


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    logger.info("on_intent requestId=" + intent_request['requestId'] +
                ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers

    if intent_name == "Activity":
        return activity(intent, session)
    elif intent_name == "Alerts":
        return alerts(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    logger.info("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    else:
        return on_session_ended(event['request'], event['session'])
