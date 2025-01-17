FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN pip install boto3
RUN mkdir /root/.aws
COPY ./credentials /root/.aws/
COPY ./app /app
