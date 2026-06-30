from __future__ import print_function
import datetime
import os.path
import os, requests, json
import importlib, subprocess, sys
def ensure_package(import_name, pip_name=None):
    pip_name = pip_name or import_name
    try:
        importlib.import_module(import_name)
        print(f"Module {import_name} is present.")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
#ensure_package("google-auth-oauthlib", "google-auth-oauthlib")
#ensure_package("google-auth-httplib2", "google-auth-httplib2")
#ensure_package("google-api-python-client", "google-api-python-client")
#ensure_package("python-dateutil", "python-dateutil")

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dateutil.relativedelta import relativedelta

SCOPE = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_254663984504-e1q46mmhq0fu3arno08fp87figch8012.apps.googleusercontent.com.json', SCOPE)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    time_min = datetime.datetime.now().isoformat()+ 'Z'
    end = datetime.datetime.now() + datetime.timedelta(days=30)
    ender = end.isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        maxResults=100,
        timeMax=ender,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    if os.path.exists('events.txt'):
        os.remove('events.txt')

    events = events_result.get('items', [])

    with open('events.txt', 'w', encoding='Latin1') as f:
        f.write("=== Eventos do dia ===\n")
        if not events:
            f.write("Nenhum evento encontrado!")
            print('Nenhum evento encontrado.')
            return
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            line = f"{start} {event['summary']}\n"
            f.write(line)
            print(start, event['summary'])

if __name__ == '__main__':
    main()

    
