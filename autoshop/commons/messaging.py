# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
import json
import string
from random import choice, randint
from threading import Thread

from flask import current_app, flash, request, session
from requests import get, post


def random_pin():
    min_char = 4
    max_char = 5
    allchar = string.digits
    pin = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
    return pin


def send_sms_async(receiver, text_body):
    Thread(
        target=sms_async, args=(current_app._get_current_object(), receiver, text_body)
    ).start()


def sms_async(app, receiver, msgtext):
    with app.app_context():
        send_sms(receiver, msgtext)


def send_sms(receiver, msgtext):
    headers = sms_headers()
    import random

    data = {
        "account_code": current_app.config["SMS_CODE"],
        "to": receiver,
        "transaction_id": str(random.randint(10000, 99999)),
        "text": msgtext,
    }

    current_app.logger.info(data)

    rep = post(current_app.config["SMS_URL"], data=json.dumps(data), headers=headers)

    current_app.logger.info(rep.status_code)

    if rep.status_code == 401:
        headers = sms_headers()
        rep = send_sms(receiver, msgtext)

    result = json.loads(rep.content.decode("utf-8"))
    current_app.logger.info(result)


def sms_headers():
    auth_token = current_app.config["SMS_AUTH_TOKEN"]

    if auth_token != "":
        return {
            "content-type": "application/json",
            "authorization": "Bearer %s" % current_app.config["SMS_AUTH_TOKEN"],
        }

    data = {
        "email": current_app.config["SMS_AUTH_KEY"],
        "password": current_app.config["SMS_AUTH_PASS"],
    }

    rep = post(
        current_app.config["SMS_AUTH_URL"],
        data=json.dumps(data),
        headers={"content-type": "application/json"},
    )

    result = json.loads(rep.content.decode("utf-8"))

    current_app.config["SMS_AUTH_TOKEN"] = result["token"]
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % result["token"],
    }
