FROM python:3.10-alpine as base
RUN apk update && apk upgrade

RUN mkdir -p /app

WORKDIR /app

ADD requirements.txt .

RUN pip install -r requirements.txt

COPY src .

EXPOSE 9182

USER nobody

ENTRYPOINT [ "python" ]

CMD [ "/app/main.py" ]
