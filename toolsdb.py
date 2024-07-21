import pymysql as sql
from cnf import config

def init_db():
    initdbconn = sql.connections.Connection(user=config['username'], password=config['password'], host=config['host'])
    with initdbconn.cursor() as cursor:
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {config["username"]}__sodium-bot-db;')
        cursor.execute(f'USE {config["username"]}__match_and_split;')
        cursor.execute('''CREATE TABLE IF NOT EXISTS `npp_notifications` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `page_name` VARCHAR(255) NOT NULL,
            `username` VARCHAR(255) NOT NULL,
            `afd` VARCHAR(255) NOT NULL,
            `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        )''')
    initdbconn.close()
    
def get_conn():
    init_db()
    dbconn = sql.connections.Connection(user=config['username'], password=config['password'], host=config['host'], database=f'{config["username"]}__sodium-bot-db')
    return dbconn
