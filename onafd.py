import json
import requests as r
import re
from notify import send_notification
from sseclient import SSEClient as EventSource

API_URL = 'https://en.wikipedia.org/w/api.php'
EVENTSTREAM_URL = 'https://stream.wikimedia.org/v2/stream/recentchange'

AFD_ARTICLE_EXTRACTION_REGEX = r'''===\[\[:([^\]]+)\]\]===\n{{REMOVE THIS TEMPLATE WHEN CLOSING THIS AfD'''
SHOULD_NOT_SEND_NOTIF = r'''({{[Nn]obots}}|\[\[Category:Wikipedians who opt out of message delivery|{{User:SodiumBot/NoNPPDelivery}})'''

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

    parameters = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "revids": revid,
        "formatversion": "2",
        "rvprop": "content",
        "rvslots": "main"
    }
    
    response = r.post(API_URL, data=parameters, headers={'X-User-Agent': 'AFD_NPP_Notifier_Bot/1.0'}, timeout=10)
    if response.status_code == 200:
        try:
            queryjson = response.json()
            wikitext = queryjson['query']['pages'][0]['revisions'][0]['slots']['main']['content']
            retitle = re.search(AFD_ARTICLE_EXTRACTION_REGEX, wikitext, re.MULTILINE | re.DOTALL)
            return retitle.group(1)
        except Exception as e:
            print(e)
            return None
    else:
        return None
    
def get_page_wikitext(pagename):
    parameters = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": pagename,
        "formatversion": "2",
        "rvprop": "content",
        "rvslots": "main"
    }
    
    response = r.post(API_URL, data=parameters, headers={'X-User-Agent': 'AFD_NPP_Notifier_Bot/1.0'}, timeout=10)
    if response.status_code == 200:
        try:
            queryjson = response.json()
            return queryjson['query']['pages'][0]['revisions'][0]['slots']['main']['content']
        except Exception as e:
            print(e)
            return None
    else:
        return None
    
def filter_notify(list_users, nominator, page_name):
    PREVIOUS_NOTIF = r'''(==Nomination of \[\[:''' + page_name + r'''\]\] for deletion==|==Deletion discussion about \[\[''' + page_name + r'''\]\]==)'''
    users_to_notify = []
    for user in list_users:
        if user == nominator:
            continue
        talk_page_wikitext = get_page_wikitext('User talk:' + user)
        if re.search(SHOULD_NOT_SEND_NOTIF, talk_page_wikitext, re.DOTALL | re.MULTILINE):
            continue
        if re.search(PREVIOUS_NOTIF, talk_page_wikitext, re.DOTALL | re.MULTILINE):
            continue
        users_to_notify.append(user)
    return users_to_notify


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
            if change['wiki'] == 'enwiki':
                if 'Wikipedia:Articles for deletion/' in change['title'] and change['type'] == 'new':
                    page_name = parse_wikitext_and_get_page(change['revision']['new'])
                    if page_name:
                        list_users = get_reviewer(page_name)
                        list_users = filter_notify(list_users, change['user'], change['title'])
                        for user in list_users:
                            send_notification(user, page_name, change['title'])
                    print(event.id)
