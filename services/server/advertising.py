"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 12:04
@Author  : zb
@File    : advertising.py
@Software: PyCharm
"""
import os

if os.environ.get('server_api_env') == 'pro':
    pre_env = '正式环境'
elif os.environ.get('server_api_env') == 'sandbox':
    pre_env = '沙盒环境'
else:
    pre_env = '测试环境'

from sanic.request import Request
from sanic.response import json
from sanic.views import HTTPMethodView

from services.server.tools import check_params, get_advertising_list, get_ad_screen_list, notice_robot, \
    get_ad_review_list, change_ad_status, handle_ad_inventory
from base.middleware import namespace
from config import conf


class AdSpaceExpendInfoReportView(HTTPMethodView):
    """广告位消耗情况上报"""

    async def post(self, request: Request):
        args = request.json
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        as_space_ids = args.get("as_id_list")
        if len(as_space_ids) > 10000:
            return json({"code": 417})
        await handle_ad_inventory(as_space_ids)
        return json({"code": 200, "data": {}})


class AdListView(HTTPMethodView):
    """获取广告列表"""

    async def get(self, request: Request):
        args = request.args
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        page = args.get("page")
        page_size = args.get("page_size")
        if not page or not page_size:
            return json({"code": 404})
        page = int(page)
        page_size = int(page_size)
        if page < 1 or page_size > 1000:
            return json({"code": 407})
        data = await get_advertising_list(request.app.ctx.rpc, channel_id, page, page_size)
        return json({"code": 200, "data": data})


class AdDeviceListView(HTTPMethodView):
    """获取广告对应设备列表"""

    async def get(self, request: Request):
        args = request.args
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        page = args.get("page")
        page_size = args.get("page_size")
        ad_id = args.get("ad_id")
        if not page or not page_size or not ad_id:
            return json({"code": 404})
        page = int(page)
        page_size = int(page_size)
        ad_id = int(ad_id)
        if page < 1 or page_size > 1000:
            return json({"code": 407})
        data = await get_ad_screen_list(request.app.ctx.rpc, channel_id, ad_id, page, page_size)
        return json({"code": 200, "data": data})


class AdPlayReportView(HTTPMethodView):
    """广告播放记录上报"""

    async def put(self, request: Request):
        args = request.json
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        records = args.get("records")
        if len(records) > 10000:
            return json({"code": 600, "data": {}, "message": "超过最大上报数量"})
        log = []
        for play in records:
            log.append({
                "playId": play.get("play_id"), "duration": play.get("duration"), "ad_id": play.get("ad_id"),
                "endPlayStatus": play.get("status"), "startPlayTime": play.get('start'),
                "device_id": play.get('device_id')
            })
        value = {"eventType": 9, "log": log}
        try:
            await namespace.kafka_producer.send(conf.KAFKA_TOPIC, value=value)
        except Exception as e:
            task_info = f'警告:\n\n项目所处环境:\t{pre_env}\n\n-曝光记录批量写入kafka: 失败\n-记录数: {len(records)}\n-渠道ID: {channel_id}\n-错误信息: {e}\n'
            await notice_robot(task_info)
            return json({"code": 500, "data": {}})
        return json({"code": 200, "data": {}})


class AdReviewView(HTTPMethodView):

    async def put(self, request: Request):
        """广告审核状态更新"""
        args = request.json
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        ad_id = args.get("ad_id")
        review_status = args.get("review_status")
        reason = args.get("reason", "")
        result = await change_ad_status(channel_id, ad_id, review_status, reason)
        if not result:
            return json({"code": 500, "data": {}})
        return json({"code": 200, "data": {}})


class AdReviewListView(HTTPMethodView):

    async def get(self, request: Request):
        """获取广告审核列表"""
        args = request.args
        channel_id = args.get("channel_id")
        ts = args.get("ts")
        checksum = args.get("checksum")
        result, code = await check_params(channel_id, ts, checksum)
        if not result:
            return json({"code": code})
        review_status = args.get("review_status")
        page = args.get("page")
        page_size = args.get("page_size")
        if not page or not page_size:
            return json({"code": 404})
        page = int(page)
        page_size = int(page_size)
        data = await get_ad_review_list(request.app.ctx.rpc, channel_id, review_status, page, page_size)
        return json({"code": 200, "data": data})
