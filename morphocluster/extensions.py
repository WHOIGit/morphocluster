"""
Created on 23.05.2018

@author: mschroeder
"""

import os.path

from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_rq2 import RQ
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import StaticPool

# StaticPool: Use one connection throughout  
database = SQLAlchemy()
redis_lru = FlaskRedis(config_prefix="REDIS_LRU")
migrate = Migrate()
rq = RQ()
