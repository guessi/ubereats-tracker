#!/usr/bin/env python3

import json
import requests
import requests_random_user_agent
import yaml

from requests.structures import CaseInsensitiveDict
from urllib.parse import quote


def slack(message: str, webhook: str) -> None:
    msg = '{"text": "' + message + '"}'
    msg = msg.encode('utf-8')

    headers = CaseInsensitiveDict()
    headers["content-type"] = "application/json"

    requests.post(webhook, headers=headers, data=msg)


def compose_headers(location: str, template: str) -> dict:
    headers = CaseInsensitiveDict()
    headers["x-csrf-token"] = "x"
    headers["content-type"] = "application/json"

    # HINT: required but I don't know why...
    address = quote(location, "utf-8")
    cookie = template.format(address)

    headers["cookie"] = cookie

    return headers


def compose_payload(store: str) -> str:
    data = {}
    data["storeUuid"] = store

    # HINT: don't remove this line, or it will be break
    data = str(data).replace("'", "\"").replace(" ", "")

    return data


def query_store_status(store: str, headers: dict) -> (str, str):
    url = "https://www.ubereats.com/api/getStoreV1?localeCode=tw"
    payload = compose_payload(store)

    s = requests.Session()
    resp = s.post(url, headers=headers, data=payload)

    store_data = json.loads(resp.text)['data']

    store_slug = store_data['slug']
    store_status = bool(store_data['isOpen'])

    return store_slug, store_status


def main():
    with open('config.yml', 'r') as stream:
        cfg = yaml.safe_load(stream)

    slack_webhook = cfg['slack_webhook']
    stores = cfg['store_uuid_list']
    location = cfg['from_location']
    template = cfg['cookie_template']
    slack_notification = bool(cfg['slack_notification'])

    headers = compose_headers(location, template)

    slack_message = ""

    for store in stores:
        name, status = query_store_status(store, headers)

        slack_message += "`{}` {}\n".format(
            name,
            "營業中 :man-gesturing-ok:"
            if status
            else "關門中 :man-gesturing-no:")

    if slack_notification is True:
        slack(slack_message, slack_webhook)
    else:
        print(slack_message)


if __name__ == '__main__':
    main()
