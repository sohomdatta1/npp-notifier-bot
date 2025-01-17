import json
import requests as r
import re
import json
from sseclient import SSEClient as EventSource
import datetime
import os
from toolsdb import get_conn
LEEND_DATE = datetime.datetime.now() - datetime.timedelta(days=2*365)

API_URL = 'https://en.wikipedia.org/w/api.php'
EVENTSTREAM_URL = 'https://stream.wikimedia.org/v2/stream/recentchange'

AFD_ARTICLE_EXTRACTION_REGEX = r'''===\[\[:([^\]]+)\]\]===\n{{REMOVE THIS TEMPLATE WHEN CLOSING THIS AfD'''

def get_reviewer(pagename):
    actions = ["pagetriage-curation/reviewed-article", "pagetriage-curation/reviewed"]
    logevents = []
    for action in actions:
        parameters = {
            "action": "query",
            "format": "json",
            "list": "logevents",
            "formatversion": "2",
            "leprop": "user",
            "letype": "pagetriage-curation",
            "leaction": action,
            "letitle": pagename
        }

        response = r.post(API_URL, data=parameters, headers={'X-User-Agent': 'AFD_NPP_Notifier_Bot/1.0'}, timeout=10)
        if response.status_code == 200:
            try:
                queryjson = response.json()
                logevents += queryjson['query']['logevents']
            except Exception as e:
                print(e)
        else:
            pass
    if len(logevents) > 0:
        users = []
        for logevent in logevents:
            users.append(logevent['user'])
        return users
    else:
        return []

def parse_wikitext_and_get_page(revid):
    print('REV: ', revid)
    parameters = {
        "action": "parse",
        "format": "json",
        "oldid": revid,
        "formatversion": "2",
        "prop": "wikitext",
        #"leend": LEEND_DATE.strftime('%Y-%m-%dT%H:%M:%SZ'),
        #"rvslots": "main"
    }
    
    response = r.post(API_URL, data=parameters, headers={'X-User-Agent': 'AFD_NPP_Notifier_Bot/1.0'}, timeout=10)
    if response.status_code == 200:
        try:
            queryjson = response.json()
            wikitext = queryjson['parse']['wikitext']
            print(wikitext)
            retitle = re.search(AFD_ARTICLE_EXTRACTION_REGEX, wikitext, re.MULTILINE)
            return retitle.group(1)
        except Exception as e:
            print(e)
            return None
    else:
        return None

for event in EventSource(EVENTSTREAM_URL, last_id=None):
    if event.event == 'message':
        try:
            change = json.loads(event.data)
        except ValueError:
            pass
        else:
            # discard canary events
            if change['meta']['domain'] == 'canary':
                continue
            if change['wiki'] == 'enwiki' or change['wiki'] == 'testwiki':
                if 'Wikipedia:Articles for deletion/' in change['title'] and change['type'] == 'new':
                    page_name = parse_wikitext_and_get_page(change['revision']['new'])
                    user = change['user']
                    if page_name:
                        list_users = get_reviewer(page_name)
                        list_users = list(set(list_users))
                        while user in list_users: list_users.remove(user)
                        list_of_notifications = []
                        for user in list_users:
                            print('To notify: ', user)
                            list_of_notifications.append({
                                "user": user,
                                'page_name': page_name,
                                'afd_link': change['title']
                            })
                        print("List of folks to notify:", list_of_notifications)
                        print(event.id)
                        with get_conn() as conn:
                            with conn.cursor() as cur:
                                for notification in list_of_notifications:
                                    cur.execute(
                                        "INSERT INTO npp_notifications (username, page_name, afd_link) VALUES (%s, %s, %s)", 
                                        (notification['user'], notification['page_name'], notification['afd_link'])
                                    )
                                print("Commiting")
                            conn.commit()