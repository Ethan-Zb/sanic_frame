"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 11:39
@Author  : zb
@File    : app.py
@Software: PyCharm
"""
import os
import traceback

from sanic import Sanic, response
from loguru import logger
from sanic.handlers import ErrorHandler
from tortoise.contrib.sanic import register_tortoise

import settings
from base import router
from config import conf


class CustomErrorHandler(ErrorHandler):
    def default(self, request, exception):
        code = getattr(exception, 'status_code', 500)
        msg = traceback.format_exc() if request.app.debug else repr(exception)
        return response.json({'code': code, 'msg': msg})


def setup(_app: Sanic):
    """注册app功能
    :param _app:
    :return:
    """
    # 注册路由
    router.register(_app, *settings.AUTO_DISCOVERY)

    # 数据库
    # register_tortoise(_app, db_url=conf.DB_URL, modules={"dsp": ["models.dsp"]}, generate_schemas=False)
    register_tortoise(_app, config=conf.DATABASE)

    # 启用中间件和监听事件
    # 绑定相关变量
    for i in dir(settings):
        if not i.startswith('__'):
            _app.config[i] = getattr(settings, i)
    # 异常的返回格式
    _app.config.FALLBACK_ERROR_FORMAT = 'json'
    _app.error_handler = CustomErrorHandler()
    logger.add('logs/service_{time}.log', enqueue=True, rotation='128 MB',
               compression='zip', retention='10 days')


if __name__ == "__main__":
    os.environ.setdefault('APP_NAME', 'server_api')
    app = Sanic(os.environ.get('APP_NAME'))
    app.extend(config=settings.EXT_CONFIG)
    setup(app)
    app.run(**settings.APP_CONFIG)
