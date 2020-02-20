# general configuration
KEYWORDS = ['苏宁', '易购', 'suning', 'sn', '双11', '双十一']
PAGES = 51
BEGIN_OFFSET = 1
END_OFFSET = 50

# Cookie池URL
COOKIE_POOL_URL = 'http://127.0.0.1:5000/weibo/random'
GET_WEIBO_COOKIE_CMD = 'curl http://127.0.0.1:5000/weibo/random'

# mysql configuration
MYSQL_HOST = '*'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '*'
MYSQL_PORT = 3306
MYSQL_DATABASE = '*'
MYSQL_TABLE = '*'

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS weibo_weibo(
id VARCHAR(255) NOT NULL,
keyword VARCHAR(255) NOT NULL,
source VARCHAR(50) NOT NULL,
comment TEXT,
title TEXT,
url VARCHAR(255) NOT NULL,
crawl_date VARCHAR(255) NOT NULL,
PRIMARY KEY(id)
)ENGINE=INNODB CHARSET=UTF8"""
