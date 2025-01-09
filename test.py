from toolsdb import get_conn

test_notifications = [
    {'user': 'TestUser1', 'page_name': 'TestPage1', 'afd_link': 'TestLink1'},
    {'user': 'TestUser2', 'page_name': 'TestPage2', 'afd_link': 'TestLink2'},
]
with get_conn() as conn:
    with conn.cursor() as cur:
        for notification in test_notifications:
            cur.execute(
                "INSERT INTO npp_notifications (username, page_name, afd_link) VALUES (%s, %s, %s)",
                (notification['user'], notification['page_name'], notification['afd_link'])
            )
        conn.commit()