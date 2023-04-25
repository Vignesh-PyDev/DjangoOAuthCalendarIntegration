from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
from datetime import datetime
import pytz
import datetime


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_FILE = "/home/vigneshwarann/Pictures/GoogleCalendarIntegration/googlecalendarintegrationtask/integrationapp/credentials.json"

#Scope is a mechanism in OAuth 2.0 to limit an application's access to a user's account.
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']
# Redirect URLs are a critical part of the OAuth flow.
# After a user successfully authorizes an application, the authorization server will redirect the user back to the application.
# Because the redirect URL will contain sensitive information,
# it is critical that the service doesn’t redirect the user to arbitrary locations.

REDIRECT_URL = 'http://127.0.0.1:8000/app/v1/calendar/redirect'
# API_SERVICE_NAME,It tells what service that we are going to use,in this case we are using calendar.
API_SERVICE_NAME = 'calendar'

API_VERSION = 'v3'


@api_view(['GET'])
def GoogleCalendarInitView(request):
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = REDIRECT_URL

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    request.session['state'] = state
    # print(state)

    return Response({"authorization_url": authorization_url})


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = request.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URL

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)


    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    # credentials in a persistent database instead.
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    # Check if credentials are in session
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])


    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Returns the calendars on the user's calendar list
    calendar_list = service.calendarList().list().execute()



    # Getting all events associated with a user ID (email address)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events  = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
    # print(events)

    events_list_append = []
    events_dict = {}
    if not events['items']:
        print('No data found.')
        return Response({"message": "No data found or user credentials invalid."})
    else:
        # Enable this to get all calendar events
        # for events_list in events['items']:
        #     events_list_append.append(events_list)
        #     return Response({"events": events_list_append})
        # return Response({"error": "calendar event aren't here"})
        for events_list in events['items']:
            print(events_list['summary'])
            events_dict["Owner"] = events_list['creator']
            events_list["Event Type"] = events_list['kind']
            events_dict["Event Description"] = events_list["summary"]
            events_dict['Event Created On'] = (events_list["created"])
            events_dict["Is Updated"] = True if events_list["updated"] else False
            events_dict['Event Updated On'] = (events_list["updated"])
            events_dict['Event Status'] = events_list["status"]
            events_dict["Event Organiser"] = events_list['organizer']
            start_time = format_date(events_list['start']['dateTime'])
            end_time = format_date(events_list['end']['dateTime'])
            events_dict["Event Starts On"] = start_time
            events_dict["Event Ends On"] = end_time
            events_dict["Duration"] = str(end_time - start_time)
            # # alUID is a key component of the iCalendar format, and is critical
            # for ensuring that calendar data can be shared and synchronized between
            # different applications and systems.
            events_dict["iCalUID"] = events_list['iCalUID']

            '''In the context of calendar APIs, the sequence is a numeric value that is associated
            with each event or task.It represents the version of the event or task, 
            and is used to track changes made to the event or task over time.
            When an event or task is created, it is assigned a sequence number of 0.
            When changes are made to the event or task, the seqence no is incremented by 1
            for each change.This allows calendar applications to track the version history of the event or task, 
            and to ensure that changes are synchronized correctly across different systems.'''

            events_dict['No of Updations Made'] = events_list['sequence']
            attendees = events_list.get('attendees',0)
            if attendees != 0:
                events_dict['Total Participants'] = len(attendees)
                events_dict['StatusOfInvite'] = get_response_status(attendees)
            else:
                events_dict['Total Participants'] = 0
                events_dict['StatusOfInvite'] = 0
            events_dict["attendees"] = attendees
            events_dict["App Name"] = events_list["conferenceData"]["conferenceSolution"]["name"]
            events_dict["Meeting URL"] = events_list["hangoutLink"]
            events_dict["MeetingID"] = events_list["conferenceData"]["conferenceId"]
            if events_list["reminders"]["useDefault"] == True:
                events_dict["Default Remainder"] = True
                events_dict['Remainder'] = 30
            else:
                events_dict["Default Remainder"] = False
                events_dict['Remainder'] = events_list['reminders']['overrides'][0]["minutes"]

            events_list_append.append(dict(events_dict))

        return Response({"events": events_list_append})
    return Response({"error": "calendar event aren't here"})

format_date = lambda _date:datetime.datetime.strptime(_date, "%Y-%m-%dT%H:%M:%S%z")

def get_response_status(argv):
    result_dict = {}
    result_dict["Total_Invite_Sent"] = len(argv)
    for iter in argv:
        if iter['responseStatus'] in result_dict.keys():
            result_dict[iter['responseStatus']] += 1
        else:
            result_dict[iter['responseStatus']] = 1
    return result_dict
def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
