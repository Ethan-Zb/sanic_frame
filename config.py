"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 11:39
@Author  : zb
@File    : config.py
@Software: PyCharm
"""
import os


class BaseConfig(object):
    # Mysql数据库配置信息
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://geek:123456@10.10.116.174:3306/dsp-dev1"

    # 关闭数据库修改跟踪操作
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 输出底层执行的sql语句
    SQLALCHEMY_ECHO = True

    # Redis数据库配置信息
    REDIS_HOST = ""
    REDIS_PORT = 6379

    # 限定允许访问的域名, 不设置则全部允许
    # CORS_ORIGINS = ['http://127.0.0.1:5000']

    KAFKA_BROKERS = []
    RedisConfig = {
        'host': "",
        'password': "", 'db': 0,
    }

    KAFKA_TOPIC = ""

    DB_URL = ""

    DING_DING_URL = ""

    DATABASE = {}
    CE_KEY_DICT = {}
    PAGE_FROM = 0
    PAGE_TO = 100
    FAILURE = 3


class DevelopmentConfig(BaseConfig):
    """开发环境的配置类"""
    DEBUG = True
    DATABASE = {
        "connections": {
            "dsp": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "database": "bubblepop_master",
                    "host": "127.0.0.1",
                    "port": 3306,
                    "user": "root",
                    "password": "123456",
                    "maxsize": 10
                }
            },
        },
        "apps": {
            "dsp": {
                "models": ["models.dsp"],
                'default_connection': 'dsp'
            }
        },
        'use_tz': False,
        'timezone': 'Asia/Shanghai'
    }
    CE_KEY_DICT = {
        4: "0XZIKX1NA33HSUXU",
        11: "IMTOCBTPJEMVLR2CFIIUWFCN6FVFRI45"  # 汇屏
    }


class ProductionConfig(BaseConfig):
    """生产环境的配置类"""
    DEBUG = False


class SandboxConfig(BaseConfig):
    """沙盒环境的配置类"""
    DEBUG = False


# 保留配置字典方便别的模块调用
config_dict = {
    "dev": DevelopmentConfig,
    "pro": ProductionConfig,
    "sandbox": SandboxConfig
}

conf: BaseConfig = config_dict.get(os.environ.get('server_api_env', 'dev').lower(), DevelopmentConfig)
