FROM python:3.9.10-slim-bullseye

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir

EXPOSE 8000

CMD ["python", "app.py"]
