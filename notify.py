import pywikibot
msg_text = "==Nomination of [[:ArticleName]] for deletion==\n{{subst:User:SodiumBot/ReviewerAfdNotification|article=ArticleName|afd=ArticleForDeletionDiscussionLink}} ~~~~"

def send_notification(username, pagename, afd_link):
    msg = msg_text.replace('ArticleName', pagename).replace('ArticleForDeletionDiscussionLink', afd_link)
    return notify(username, msg)

def notify(username, message):
    print(f"Sending notification to {username}: {message}")
    site = pywikibot.Site('en', 'wikipedia')
    user_talk_page = pywikibot.Page(site, f"User talk:{username}")
    user_talk_page.text += f"\n{message}"
    user_talk_page.save("Notifying new page reviewer of AFD nomination")
    return True