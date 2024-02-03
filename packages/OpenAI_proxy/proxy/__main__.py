import json
import logging
from logging.handlers import SysLogHandler
import os

import requests
import sentry_sdk

syslog = SysLogHandler(address=('logs6.papertrailapp.com', 20625))
format = '%(asctime)s shortcut-assistant: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.DEBUG)

PROMPT = """You help make sure that tickets are ready for development. What sorts of technical questions should I ask before beginning development. The basic fundamentals of our application are already setup and not open questions (database, etc). Do not ask questions about the following: 1. Unit Testing 2. Basic Architecture Setup (Database, etc) 3. Deadlines 4) Concurrency
    \n\nExamples of good questions: - Are there performance or scalability requirements or considerations for the feature?' - What user roles and permissions need to be accounted for within this feature? - What new monitoring or alerting should be put in place? - Should we consider implementing a feature flag' - Have all instances where the deprecated model is used been identified
    \n\nExamples of bad questions: - What are the technical and business requirements for the feature?(too broad) - How will the system access and query the Customers database?(implementation already known) - What are the specific user story requirements and how do they align with the broader application requirements? (too broad)
    \n\nGive the top 5 questions in a concise manner, just state the questions without any intro."""

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


def main(event, context):
    context = {
        "body": {
            "event": event,
            "context": {
                "activationId": context.activation_id,
                "apiHost": context.api_host,
                "apiKey": context.api_key,
                "deadline": context.deadline,
                "functionName": context.function_name,
                "functionVersion": context.function_version,
                "namespace": context.namespace,
                "requestId": context.request_id,
            },
        },
    }
    logging.debug(context)
    logging.debug(event)
    description = event.get('description')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ["OPENAI_API_TOKEN"]}',
    }

    requestBody = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": description
            }
        ]
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers,
                             data=json.dumps(requestBody))
    try:
        logging.debug(response.json())
    except Exception as e:
        logging.exception(e)
    response_json = response.json()
    content = response_json.get('choices')[0]['message']['content']
    proxy_response = {'body': {'description': description, 'content': content}}
    logging.debug(proxy_response)
    return proxy_response
