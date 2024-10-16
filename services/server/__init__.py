"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 12:05
@Author  : zb
@File    : __init__.py.py
@Software: PyCharm
"""
from sanic import Blueprint

from .advertising import AdSpaceExpendInfoReportView, AdListView, AdDeviceListView, AdPlayReportView, AdReviewView, \
    AdReviewListView

screen_api = Blueprint("screen_api", url_prefix="/v1/s2s")
screen_api.add_route(AdSpaceExpendInfoReportView.as_view(), "/inventory")
screen_api.add_route(AdListView.as_view(), "/ad_list")
screen_api.add_route(AdDeviceListView.as_view(), "/ad_device_list")
screen_api.add_route(AdPlayReportView.as_view(), "/play")
screen_api.add_route(AdReviewView.as_view(), "/review")
screen_api.add_route(AdReviewListView.as_view(), "/review_list")
