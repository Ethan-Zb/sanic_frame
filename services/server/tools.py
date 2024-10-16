"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/24 17:58
@Author  : zb
@File    : tools.py
@Software: PyCharm
"""
import time
import asyncio
from datetime import datetime, timedelta
import hashlib
import json
import os
import traceback

if os.environ.get('server_api_env') == 'pro':
    pre_env = '正式环境'
elif os.environ.get('server_api_env') == 'sandbox':
    pre_env = '沙盒环境'
else:
    pre_env = '测试环境'

from tortoise.queryset import Q
from tortoise.transactions import in_transaction
from base.middleware import namespace
from services.protobuf import api_pb2 as pb2
from models.dsp import Advertisement, AdvertisingSpace, ScreenInventory, LockedInventory, ScreenBusiness
from config import conf


async def check_params(channel_id, ts, checksum):
    """校验参数"""
    screen_business = await ScreenBusiness.filter(sb_id=channel_id).first()
    if not screen_business:
        return False, 404
    print(f"{screen_business.sb_dock_type, type(screen_business.sb_dock_type)}: screen_business.sb_dock_type")
    if screen_business.sb_dock_type == 1:
        return True, 200
    if not channel_id or not ts or not checksum:
        return False, 404
    # 校验时间戳
    if int(time.time() * 1000) - int(ts) > 6000000:
        return False, 405
    # 校验校验码
    ck_key = screen_business.sb_ck_key
    new_checksum = str(channel_id) + str(ts) + ck_key
    md5 = hashlib.md5()
    md5.update(new_checksum.encode())
    new_checksum_md5 = md5.hexdigest()
    if new_checksum_md5 != checksum:
        return False, 401
    return True, 200


async def notice_robot(content):
    """钉钉机器人"""
    url = conf.DING_DING_URL
    headers = {'Content-Type': 'application/json'}
    data = {'msgtype': 'text', 'text': {'content': content}, 'at': {'atMobiles': [], 'isAtAll': False}}
    response = await namespace.http_client.post(url=url, data=json.dumps(data), headers=headers)
    result = json.loads(response.content.decode())
    if result.get('errcode') != 0:
        print('[{}] DingDing alarm failed, msg: {}'.format(
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), result.get('errmsg')))
        return False
    return True


async def get_advertising_list(rpc_client, channel_id, page, page_size):
    """获取广告列表"""
    try:
        response = await rpc_client.ad_list(
            pb2.ServerAdListRequest(channel_id=int(channel_id), page=page, page_size=page_size))
        total_page = response.total_page
        page = response.page
        total = response.total
        ad_list = response.ad_list
        new_ad_list = []
        for ad in ad_list:
            media_list = get_media_list(ad.media_list)
            new_ad_list.append({
                "ad_id": ad.ad_id,
                "play_id": ad.play_id,
                "device_count": ad.device_count,
                "status": ad.status,
                "update_ts": ad.update_ts,
                "begin": ad.begin,
                "end": ad.end,
                "expired": ad.expired,
                "media_list": media_list
            })
        data = {"total_page": total_page, "page": page, "total": total, "ad_list": new_ad_list}
        return data
    except Exception as e:
        task_info = f'警告:\n\n项目所处环境:\t{pre_env}\n\n-获取广告列表: 失败\n-渠道ID: {channel_id}\n-错误信息: {e}\n'
        traceback.print_exc()
        await notice_robot(task_info)
        return []


async def get_ad_screen_list(rpc_client, channel_id, ad_id, page, page_size):
    """获取广告对应设备列表"""
    try:
        response = await rpc_client.ad_screens(
            pb2.ServerAdScreensRequest(channel_id=int(channel_id), ad_id=ad_id, page=page, page_size=page_size))
        total_page = response.total_page
        page = response.total_page
        total = response.total
        device_list = response.device_list
        new_device_list = []
        for device in device_list:
            new_device_list.append({"device_id": device.device_id, "count": device.count})
        data = {"total_page": total_page, "page": page, "total": total, "device_list": new_device_list}
        return data
    except Exception as e:
        task_info = f'警告:\n\n项目所处环境:\t{pre_env}\n\n-获取广告对应设备列表: 失败\n-渠道ID: {channel_id}\n-广告ID: {ad_id}\n-错误信息: {e}\n'
        traceback.print_exc()
        await notice_robot(task_info)
        return []


async def get_ad_review_list(rpc_client, channel_id, review_status, page, page_size):
    """获取广告审核列表"""
    try:
        response = await rpc_client.review_list(pb2.ServerReviewListRequest(
            channel_id=int(channel_id), review_status=int(review_status), page=page, page_size=page_size))
        total_page = response.total_page
        page = response.page
        total = response.total
        ad_list = response.ad_list
        new_ad_list = []
        for ad in ad_list:
            media_list = get_media_list(ad.media_list)
            new_ad_list.append({
                "ad_id": ad.ad_id,
                "review_status": ad.review_status,
                "update_ts": ad.update_ts,
                "begin": ad.begin,
                "end": ad.end,
                "expired": ad.expired,
                "media_list": media_list
            })
        data = {"total_page": total_page, "page": page, "total": total, "ad_list": new_ad_list}
        return data
    except Exception as e:
        task_info = f'警告:\n\n项目所处环境:\t{pre_env}\n\n-获取广告审核列表: 失败\n-渠道ID: {channel_id}\n-错误信息: {e}\n'
        traceback.print_exc()
        await notice_robot(task_info)
        return []


async def change_ad_status(channel_id, ad_id, review_status, reason):
    """修改广告审核状态"""
    try:
        ad = await Advertisement.filter(id=ad_id).prefetch_related("ad_group__ad_project__user").first()
        if not ad:
            return False
        review_status_dict = ad.review_status
        if review_status_dict:
            review_status_dict[channel_id] = int(review_status)
            ad.review_status = review_status_dict
        else:
            ad.review_status = {channel_id: int(review_status)}
        if int(review_status) == conf.FAILURE:
            review_list = ad.review_reason
            review_dict = {channel_id: reason, "review_ts": int(time.time() * 1000)}
            if review_list:
                for i in review_list:
                    if i.get(channel_id):
                        review_list.remove(i)
                review_list.append(review_dict)
            else:
                ad.review_reason = [review_dict]
        await ad.save()
        key = "dsp:%s:gd:tasks" % os.environ.get('server_api_env', "dev")
        task = {
            # todo : 需要加上屏商ID
            "channel_id": channel_id,
            "ad_id": ad_id,
            "ag_id": ad.ad_group_id,
            "ap_id": ad.ad_group.ad_project_id,
            "account_id": ad.ad_group.ad_project.user.account_id
        }
        await namespace.redis_conn.rpush(key, json.dumps(task))
        return True
    except Exception as e:
        task_info = f'警告:\n\n项目所处环境:\t{pre_env}\n\n-广告审核: 失败\n-广告ID: {ad_id}\n-错误信息: {e}\n'
        traceback.print_exc()
        await notice_robot(task_info)
        return False


async def handle_ad_inventory(as_space_ids):
    """
    处理广告位库存函数
    """
    p_from = conf.PAGE_FROM
    p_to = conf.PAGE_TO
    while True:
        as_space_ids = as_space_ids[p_from: p_to]
        if not as_space_ids:
            break
        add = []
        delete_list = []
        ads_gather, lock_gather, as_space_id_map_dict = handle_as_place(as_space_ids)
        await update_lock_stock(lock_gather, as_space_id_map_dict)

        *_, gather_stock = await asyncio.gather(*ads_gather)
        if not gather_stock:
            # 所有广告位在上传时间范围内都没有记录，直接新增所有广告位时间范围内的库存
            await add_as_stock(as_space_id_map_dict)
            p_from = p_to
            p_to += conf.PAGE_TO
            continue
        as_stocks = _ + [gather_stock]
        for one_as_stock_list in as_stocks:  # 每一个广告位对应的 广告位库存 对象列表
            await handle_each_as_stock(one_as_stock_list, as_space_id_map_dict, add, delete_list)
        add_list = list(set(add))
        await ScreenInventory.filter(si_id__in=delete_list).delete()
        await ScreenInventory.bulk_create(add_list)
        p_from = p_to
        p_to += conf.PAGE_TO
    return


def handle_as_place(as_space_ids):
    """处理广告位ID"""
    ads_gather = []
    lock_gather = []
    as_space_id_map_dict = {}
    for as_id_dict in as_space_ids:
        as_space_id = as_id_dict.get("as_id")
        date_begin = as_id_dict.get("date_begin")
        date_end = as_id_dict.get("date_end")
        amount = as_id_dict.get("amount")
        total = as_id_dict.get("total")
        period = (total - amount) * 3600
        st = datetime.date(datetime.strptime(date_begin, "%Y-%m-%d"))
        end = datetime.date(datetime.strptime(date_end, "%Y-%m-%d"))
        as_space_id_map_dict[as_space_id] = [st, end, period]
        ads_gather.append(ScreenInventory.filter(
            Q(ad_space__as_space_id=as_space_id) & ~Q(Q(start_date__gt=end) | Q(expiry_date__lt=st))).prefetch_related(
            "ad_space"))
        lock_gather.append(LockedInventory.filter(
            Q(ad_space__as_space_id=as_space_id) & Q(date__gte=st) & Q(date__lte=end)).prefetch_related("ad_space"))
    return ads_gather, lock_gather, as_space_id_map_dict


async def update_lock_stock(lock_gather, as_space_id_map_dict):
    """更新已锁库存"""

    async with in_transaction():
        *_, gather_lock = await asyncio.gather(*lock_gather)
        if not gather_lock:
            return
        lock_gather = _ + [gather_lock]
        for lock_stock in lock_gather:
            _, _, period = as_space_id_map_dict.get(lock_stock[0].ad_space.as_space_id)
            new_surplus_period = period - lock_stock[0].lock_period
            if new_surplus_period < 0:
                print("已锁库存大于新上传库存, 失败")
                return
            lock_stock[0].surplus_period = new_surplus_period
            await lock_stock[0].save()


async def add_as_stock(as_space_id_map_dict):
    """新增上传的所有广告位的库存记录"""
    add_list = []
    for as_space_id, l in as_space_id_map_dict.items():
        st_as, end_as, period_as = l
        as_obj = await AdvertisingSpace.filter(as_space_id=as_space_id).first()
        add_list.append(ScreenInventory(start_date=st_as, expiry_date=end_as, period=period_as, ad_space=as_obj))
    await ScreenInventory.bulk_create(add_list)


async def handle_each_as_stock(one_as_stock_list, as_space_id_map_dict, add, delete_list):
    """处理每个广告位的库存"""
    one_day = timedelta(days=1)
    as_space_id = one_as_stock_list[0].ad_space.as_space_id
    st_as, end_as, period_as = as_space_id_map_dict.get(as_space_id)
    for one_stock_obj in one_as_stock_list:
        # 在上传时间范围内有记录的广告位
        as_obj = one_stock_obj.ad_space
        add.append(ScreenInventory(start_date=st_as, expiry_date=end_as, period=period_as, ad_space=as_obj))
        # 上传库存区间包含原有库存区间
        if one_stock_obj.start_date >= st_as and one_stock_obj.expiry_date <= end_as:
            delete_list.append(one_stock_obj.si_id)
            continue
        # 原有库存区间包含上传库存区间
        if one_stock_obj.start_date < st_as and one_stock_obj.expiry_date > end_as:
            delete_list.append(one_stock_obj.si_id)
            add.append(ScreenInventory(start_date=st_as, expiry_date=end_as - one_day,
                                       period=one_stock_obj.period, ad_space=as_obj))
            add.append(ScreenInventory(start_date=st_as + one_day, expiry_date=one_stock_obj.expiry_date,
                                       period=one_stock_obj.period, ad_space=as_obj))
            continue
        # 右侧交集
        if one_stock_obj.start_date < st_as and one_stock_obj.expiry_date <= end_as:
            delete_list.append(one_stock_obj.si_id)
            add.append(ScreenInventory(start_date=one_stock_obj.start_date, expiry_date=st_as - one_day,
                                       period=one_stock_obj.period, ad_space=as_obj))
            continue
        # 左侧交集
        if one_stock_obj.start_date > st_as and one_stock_obj.expiry_date > end_as:
            delete_list.append(one_stock_obj.si_id)
            add.append(ScreenInventory(start_date=end_as + one_day, expiry_date=one_stock_obj.expiry_date,
                                       period=one_stock_obj.period, ad_space=as_obj))
            continue


def get_media_list(media_list_obj):
    """获取广告素材列表"""
    media_list = []
    for media_obj in media_list_obj:
        media_list.append({
            "media_url": media_obj.media_url,
            "jump_url": media_obj.jump_url,
            "md5": media_obj.md5,
            "filename": media_obj.filename,
            "media_type": media_obj.media_type,
            "duration": media_obj.duration
        })
    return media_list
