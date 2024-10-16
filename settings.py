"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 11:40
@Author  : zb
@File    : settings.py
@Software: PyCharm
"""
import os

BASEDIR = os.path.dirname(__file__)

APP_CONFIG = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': True,
    'access_log': True,
    'workers': 1,
}

EXT_CONFIG = {
    'oas': True
}

CORS_ORIGINS = '*'

# 自动发现 用于注册路由、蓝图、中间件、监听事件、异步任务等
AUTO_DISCOVERY = [
    'services.server',
    'base.middleware',
]
