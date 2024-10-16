"""
!/usr/bin/env python
-*- coding: utf-8 -*-
@Time    : 2022/3/4 16:45
@Author  : zb
@File    : dsp.py
@Software: PyCharm
"""
from enum import IntEnum
from tortoise.models import Model
from tortoise import fields


class MonitorEvent(Model):
    # id = fields.BigIntField(pk=True)
    channel_id = fields.IntField()
    device_id = fields.CharField(max_length=255)
    ts = fields.CharField(max_length=255)
    play_id = fields.CharField(max_length=255)
    ad_id = fields.CharField(max_length=255)
    event_type = fields.IntField()
    event_param = fields.CharField(max_length=255)

    class Meta:
        table = "monitor_event"
        # unique_together = ("field_a", "field_b")  # 唯一字段
        # indexes = ("field_a", "field_b")  # 索引
        # ordering = ["name", "-date_field"]  # 默认排序


class Account(Model):
    a_id = fields.BigIntField(pk=True, source_field="a_id")

    class Meta:
        table = "account"

    def __str__(self):
        return self.a_id


class User(Model):
    id = fields.BigIntField(pk=True)
    account = fields.ForeignKeyField("dsp.Account", source_field="a_id", related_name="user")

    class Meta:
        table = "user"


class AdvertisementProject(Model):
    class Target(IntEnum):
        BRAND = 1
        QR_CODE = 2

    class Budget(IntEnum):
        UNLIMITED = 1
        LIMIT = 2

    ap_id = fields.BigIntField(pk=True)
    ap_name = fields.CharField(max_length=100, default=str(), null=False)
    ap_available = fields.BooleanField(default=True)
    ap_status = fields.BooleanField(default=True, null=False)
    ap_target_type = fields.IntField(
        choices=[(e.value, e.name) for e in Target], null=False)
    ap_day_budget_type = fields.IntField(
        default=Budget.UNLIMITED, choices=[(e.value, e.name) for e in Budget], null=False
    )
    ap_total_budget_type = fields.IntField(
        default=Budget.UNLIMITED, choices=[(e.value, e.name) for e in Budget], null=False
    )
    ap_day_budget = fields.FloatField(default=0, null=True)
    ap_total_budget = fields.FloatField(default=0, null=True)
    ap_note = fields.CharField(max_length=100, null=True)
    ap_create_time = fields.DatetimeField(auto_now_add=True, null=True)
    ap_update_time = fields.DatetimeField(auto_now=True, null=True)
    ap_delete_time = fields.DatetimeField(null=True)
    user = fields.ForeignKeyField('dsp.User', source_field="user_id", related_name="ad_project")

    class Meta:
        table = "advertisement_project"

    def __str__(self):
        return self.ap_name


class AdvertisementGroup(Model):
    """广告组"""

    id = fields.BigIntField(pk=True, source_field='ag_id')
    ag_name = fields.CharField(max_length=100, default='', null=True)
    # ag_available = fields.BooleanField(default=False)
    # ag_status = fields.IntField()
    # ag_note = fields.CharField(max_length=100, null=True)
    # ag_crowd = fields.JSONField(null=True)
    # ag_region_location = fields.JSONField(null=True)
    # ag_place_location = fields.JSONField(null=True)
    ag_put_cycle_type = fields.IntField()
    ag_put_start_date = fields.DateField(null=True)
    ag_put_end_date = fields.DateField(null=True)
    ag_put_start_time = fields.TimeDeltaField(null=True)
    # ag_put_end_time = TimeField(null=True)
    ag_put_time_type = fields.IntField()
    ag_pay_type = fields.IntField()
    ag_day_budget_type = fields.IntField()
    # ag_balance = fields.DecimalField(10, 3, null=True)
    # ag_price = fields.FloatField(default=0, null=True)
    # ag_day_budget = fields.FloatField(default=0, null=True)
    ag_create_time = fields.DatetimeField(auto_now_add=True, null=True)
    ag_update_time = fields.DatetimeField(auto_now=True, null=True)
    ag_delete_time = fields.DatetimeField(null=True)
    ad_project = fields.ForeignKeyField('dsp.AdvertisementProject', source_field='ap_id',
                                        related_name="ad_group")

    class Meta:
        table = "advertisement_group"

    def __str__(self):
        return f'<AdvertisementGroup {self.ag_name}>'

    @classmethod
    def ig_delete(cls, *args, **kwargs):
        """忽略已删除的广告组"""
        kwargs = {'ag_delete_time': None, **kwargs}
        return cls._meta.manager.get_queryset().filter(*args, **kwargs)


class Advertisement(Model):
    """广告创意"""

    class Meta:
        table = "advertisement"

    class Status(IntEnum):
        PROCESSING = 1
        STOP = 2
        REVIEW = 3
        NOT_PASS = 4
        WAIT_PROCESS = 5
        END_PROCESS = 6

    id = fields.BigIntField(pk=True, source_field='ad_id')
    ad_name = fields.CharField(max_length=100, default='', null=True)
    ad_note = fields.CharField(max_length=100, null=True)
    ad_available = fields.BooleanField(default=False)
    ad_status = fields.IntField()
    review_status = fields.JSONField()
    review_reason = fields.JSONField()
    ad_create_time = fields.DatetimeField(auto_now_add=True, null=True)
    ad_update_time = fields.DatetimeField(auto_now=True, null=True)
    ad_delete_time = fields.DatetimeField(null=True)
    ad_group = fields.ForeignKeyField('dsp.AdvertisementGroup', source_field='ag_id',
                                      related_name="ad")

    def __str__(self):
        return f'<Advertisement {self.ad_name}>'

    @classmethod
    def ig_delete(cls, *args, **kwargs):
        """忽略已删除的广告创意"""
        kwargs = {'ad_delete_time': None, **kwargs}
        return cls._meta.manager.get_queryset().filter(*args, **kwargs)


class Screen(Model):
    class MaterialType(IntEnum):
        VIDEO = 1
        IMAGE = 2

    s_id = fields.BigIntField(pk=True)
    s_device_id = fields.CharField(max_length=255)
    s_device_key = fields.CharField(max_length=16)
    s_uuid = fields.CharField(max_length=36)
    s_description = fields.CharField(max_length=255)
    s_unit_play = fields.IntField()
    s_unit_price = fields.DecimalField(decimal_places=3, max_digits=10)
    s_cpm_cost = fields.DecimalField(decimal_places=3, max_digits=10)
    s_cpm_price = fields.DecimalField(decimal_places=3, max_digits=10)
    s_create_time = fields.DatetimeField(auto_now_add=True)
    s_update_time = fields.DatetimeField(auto_now=True)
    s_delete_time = fields.DatetimeField()
    p_id = fields.BigIntField()

    class Meta:
        table = "screen"


class AdvertisingSpace(Model):
    as_id = fields.BigIntField(pk=True)
    screen = fields.ForeignKeyField('dsp.Screen', source_field='s_id', related_name="screen")
    as_space_id = fields.CharField(max_length=48)
    as_serial = fields.SmallIntField()
    as_material_type = fields.JSONField()
    as_video_type = fields.JSONField()
    as_image_type = fields.JSONField()
    as_material_volume = fields.CharField(max_length=50)
    as_duration = fields.JSONField()
    as_height_px = fields.IntField()
    as_width_px = fields.IntField()

    def __hash__(self):
        return hash(self.as_id)

    class Meta:
        table = "advertising_space"


class ScreenInventory(Model):
    si_id = fields.BigIntField(pk=True)
    ad_space = fields.ForeignKeyField('dsp.AdvertisingSpace', source_field='as_id', related_name="inventories")
    start_date = fields.DateField()
    expiry_date = fields.DateField()
    period = fields.IntField()

    def __hash__(self):
        return hash('%s%s%s%s' % (self.ad_space.__hash__(), self.start_date, self.expiry_date, self.period))

    class Meta:
        table = "screen_inventory"


class LockedInventory(Model):
    li_id = fields.BigIntField(pk=True)
    ad_space = fields.ForeignKeyField('dsp.AdvertisingSpace', source_field='as_id', related_name='lock_inventories')
    date = fields.DateField()
    lock_period = fields.IntField()
    surplus_period = fields.IntField()

    class Meta:
        table = "locked_inventory"


class ScreenBusiness(Model):
    sb_id = fields.BigIntField(pk=True)
    sb_name = fields.CharField(max_length=100)
    sb_dock_type = fields.IntField()
    sb_ck_key = fields.CharField(max_length=255)

    class Meta:
        table = "screen_business"
