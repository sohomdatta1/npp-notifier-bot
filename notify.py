import pywikibot
import os
import json
import re
import requests as r

API_URL = 'https://en.wikipedia.org/w/api.php'
SHOULD_NOT_SEND_NOTIF = r'''({{[Nn]obots}}|\[\[Category:Wikipedians who opt out of message delivery|{{User:SodiumBot/NoNPPDelivery}})'''

msg_text = "==Nomination of [[:ArticleName]] for deletion==\n{{subst:User:SodiumBot/ReviewerAfdNotification|article=ArticleName|afd=ArticleForDeletionDiscussionLink}} ~~~~"


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

def filter_notify(user, nominator, page_name):
    PREVIOUS_NOTIF = r'''(==Nomination of \[\[:''' + page_name + r'''\]\] for deletion==|==Deletion discussion about \[\[''' + page_name + r'''\]\]==)'''
    if user == nominator:
        return False
    talk_page_wikitext = get_page_wikitext('User talk:' + user)
    if re.search(SHOULD_NOT_SEND_NOTIF, talk_page_wikitext, re.DOTALL | re.MULTILINE):
        return False
    if re.search(PREVIOUS_NOTIF, talk_page_wikitext, re.DOTALL | re.MULTILINE):
        return False
    return True

def send_notification(username, pagename, afd_link):
    msg = msg_text.replace('ArticleName', pagename).replace('ArticleForDeletionDiscussionLink', afd_link)
    return notify(username, msg)

def notify(username, message):
    print(f"Sending notification to {username}: {message}")
    if os.environ.get( 'TOOLFORGE_ENABLE_BOT' ):
        site = pywikibot.Site('en', 'wikipedia')
        user_talk_page = pywikibot.Page(site, f"User talk:{username}")
        user_talk_page.text += f"\n{message}"
        user_talk_page.save("Notifying new page reviewer of AFD nomination")
    return True


list_notifications = json.loads(os.environ.get('TOOL_DATA_DIR') + '/NPP_users_to_notify.json')
list_notifications = filter(filter_notify, list_notifications)
for notifications in list_notifications:
    send_notification(notifications['user'], notifications['page_name'], notifications['afd_link'])