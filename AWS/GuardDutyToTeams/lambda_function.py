from __future__ import print_function

import json
import os
import urllib2

SEV_THRESHOLD = float(os.getenv('severity_threshold', 2.0))
API_URL = os.getenv('api_url')


def send_card(card):
    if API_URL is None:
        print('Would have sent card but API URL is not set')
        return
    request = urllib2.Request(API_URL)
    request.add_header('Content-type', 'application/json')
    response = urllib2.urlopen(request, json.dumps(card))
    response.close()


def lambda_handler(event, context):
    event_detail = event['detail']
    if event_detail['severity'] > SEV_THRESHOLD:
        card = {}
        card['@type'] = 'MessageCard'
        card['@context'] = 'http://schema.org/extensions'
        card['themeColor'] = 'E21D38'  # F5 Red
        card['title'] = 'GuardDuty Alert on Account {0}: {1}'.format(
            event['account'], event_detail['type'])
        # card['summary'] = event_detail['description']
        card['summary'] = 'GuardDuty Alert Sev {0} on Account {1}'.format(
            event_detail['severity'], event['account'])

        # Generate card sections
        sections = [{
            'facts': [
                {
                    'name': 'Severity',
                    'value': event_detail['severity']
                },
                {
                    'name': 'Description',
                    'value': event_detail['description']
                },
                {
                    'name': 'Type',
                    'value': event_detail['type']
                },
                {
                    'name': 'Creation Time',
                    'value': event_detail['createdAt']
                },
                {
                    'name': 'Update Time',
                    'value': event_detail['updatedAt']
                }
            ]
        }]
        card['sections'] = sections

        # Send card to teams
        send_card(card)
