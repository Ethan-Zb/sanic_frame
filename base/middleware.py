"""定义中间件"""
import os
import time
import orjson
import grpc
import aioredis
import httpx

import ujson
from loguru import logger
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from aiokafka import AIOKafkaProducer
from types import SimpleNamespace

from config import conf
from services.protobuf import api_pb2_grpc as pb2_grpc

_app = Sanic.get_app(os.getenv('screen_api'))

namespace = SimpleNamespace()


@_app.on_request
def log_middle_req(request: Request):
    """记录请求进入时间"""
    request.ctx.log_time = time.time()


@_app.before_server_start
async def init_server(_app, loop):
    options = [("grpc.lb_policy_name", "round_robin"), ]
    conn = grpc.aio.insecure_channel("dispatcher-service-balance:50051", options)
    # conn = grpc.aio.insecure_channel("192.168.2.19:50051", options)
    _app.ctx.rpc = pb2_grpc.ServerAPIStub(channel=conn)

    namespace.kafka_producer = AIOKafkaProducer(
        bootstrap_servers=conf.KAFKA_BROKERS, value_serializer=lambda x: orjson.dumps(x))
    limit = httpx.Limits(max_keepalive_connections=50, max_connections=200)
    timeout = httpx.Timeout(10, pool=20)
    namespace.http_client = httpx.AsyncClient(timeout=timeout, limits=limit)
    namespace.redis_conn = aioredis.StrictRedis(decode_responses=True, **conf.RedisConfig)
    await namespace.kafka_producer.start()


# @_app.before_server_start
async def rpc_init(_app, loop):
    options = [("grpc.lb_policy_name", "round_robin"), ]
    # conn = grpc.aio.insecure_channel("dispatcher-service-balance:50051", options)
    conn = grpc.aio.insecure_channel("192.168.2.50:50051", options)
    _app.ctx.rpc = pb2_grpc.ServerAPIStub(channel=conn)


@_app.after_server_stop
async def server_close(_app, loop):
    await namespace.kafka_producer.stop()


@_app.on_response
def log_middle_res(request: Request, response: HTTPResponse):
    duration = time.time() - request.ctx.log_time
    print(f"返回拦截: {response.body}")

    body = ujson.loads(str(response.body, 'utf8'))
    code, data = body.get('code'), body.get("data", {})
    if code == 200:
        message = "OK"
    elif code == 401:
        message = "checksum invalid"
    elif code == 403:
        message = "Device access is not allowed"
    elif code == 405:
        message = "ts invalid"
    elif code == 406:
        message = "ts repeat"
    elif code == 407:
        message = "page/page_size invalid"
    elif code == 500:
        message = "Server internal error"
    elif code == 600:
        message = body.get("message") if body.get("message") else "High server load. Try again later"
    else:
        message = "invalid params"
    response.body = bytes(ujson.dumps({"code": code, "message": message, "data": data}), encoding="utf8")

    content = {
        '请求IP': request.ip,
        '请求方式': request.method,
        '请求路径': request.path,
        'query参数': request.query_string,
        "json参数": request.json,
        '响应代码': code,
        '响应耗时': f'{duration:.3f}秒',
        # '响应大小': bytes_to_human(len(response.body)),
        '响应消息': message,
    }
    logger.info('\t'.join(f'{k}:{v}' for k, v in content.items()))
