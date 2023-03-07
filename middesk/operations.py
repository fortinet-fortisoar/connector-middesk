""" Copyright start
  Copyright (C) 2008 - 2023 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import requests
from connectors.core.connector import get_logger, ConnectorError
from connectors.core.utils import update_connnector_config

logger = get_logger('middesk')


class Middesk(object):
    def __init__(self, config):
        self.verify_ssl = config.get('verify_ssl')
        self.token = config.get("token")
        if self.token is None:
            self.get_token(config)
            self.token = config.get("token")

        self.connector_info = config.get("connector_info")
        if self.connector_info:
            update_connnector_config(connector_name=self.connector_info.get("connector_name"),
                                     version=self.connector_info.get("connector_version"),
                                     updated_config=config,
                                     configId=config.get("config_id"))

    def get_OAuth_token(self, config):
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        data = {
            "grant_type": "authorization_code",
            "code": config.get("code"),
            "client_id": config.get("client_id"),
            "client_secret": config.get("client_secret"),
            "redirect_uri": config.get("redirect_uri")
        }
        url = "https://api.middesk.com/oauth/token"
        resp = self.make_api_call(method="POST", data=data, url=url, headers=headers)
        config["token"] = resp.get("access_token")

    def make_api_call(self, method="GET", endpoint="", params=None, data=None, json_data=None):
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                'Authorization': f'Bearer {self.token}'
            }
            url = "https://api.middesk.com/v1/businesses" + endpoint
            logger.error("The payload is {0}".format(json_data))

            response = requests.request(method=method, url=url,
                                        headers=headers, data=data, json=json_data, params=params,
                                        verify=self.verify_ssl)

            if response.ok:
                return response.json()
            else:
                if response.text != "":
                    err_resp = response.json()
                    failure_msg = err_resp['errors'][0]['message']
                    error_msg = 'Response [{0}:{1} Details: {2}]'.format(response.status_code, response.reason,
                                                                         failure_msg if failure_msg else '')
                else:
                    error_msg = 'Response [{0}:{1}]'.format(response.status_code, response.reason)
                logger.error(error_msg)
                raise ConnectorError(error_msg)
        except requests.exceptions.SSLError:
            logger.error('An SSL error occurred')
            raise ConnectorError('An SSL error occurred')
        except requests.exceptions.ConnectionError:
            logger.error('A connection error occurred')
            raise ConnectorError('A connection error occurred')
        except requests.exceptions.Timeout:
            logger.error('The request timed out')
            raise ConnectorError('The request timed out')
        except requests.exceptions.RequestException:
            logger.error('There was an error while handling the request')
            raise ConnectorError('There was an error while handling the request')
        except Exception as err:
            raise ConnectorError(str(err))


def check_for_data(params):
    return {k: v for k, v in params.items() if v is not None and v != ''}


def make_list_value_params(value):
    if isinstance(value, list):
        return value
    return str(value).split()


def build_params(key, value):
    input_format = []
    value = make_list_value_params(value)
    if key == 'tags':
        return value
    for x in value:
        input_dict = {key: x}
        input_format.append(input_dict)
    return input_format


def get_businesses_list(config, params):
    MD = Middesk(config)
    params = check_for_data(params)
    return MD.make_api_call(params=params)


def get_business(config, params):
    MD = Middesk(config)
    endpoint = f"/{params.pop('id')}"
    return MD.make_api_call(endpoint=endpoint)


def update_business(config, params):
    MD = Middesk(config)
    params = check_for_data(params)
    if params.get('website'):
        params['website'] = {"url": params.pop('website')}
    if params.get('phone_numbers'):
        params['phone_numbers'] = build_params('phone_number', params.pop('phone_numbers'))
    endpoint = f"/{params.pop('id')}"
    return MD.make_api_call(method='PATCH', json_data=params, endpoint=endpoint)


def create_business(config, params):
    MD = Middesk(config)
    params = check_for_data(params)
    if params.get('tin'):
        params['tin'] = {"tin": params.pop('tin')}
    if params.get('formation'):
        params['formation'] = {"formation_state": params.pop('formation')}
    if params.get('website'):
        params['website'] = {"url": params.pop('website')}

    business_attributes = {
        'phone_numbers': 'phone_number',
        'orders': 'product',
        'tags': 'tags'
    }

    for k, v in business_attributes.items():
        if params.get(k) is not None and params.get(k) != '':
            params[k] = build_params(v, params.pop(k))
    return MD.make_api_call(method='POST', json_data=params)


def _check_health(config):
    if get_businesses_list(config, params={}):
        return True


operations = {
    'get_businesses_list': get_businesses_list,
    'get_business': get_business,
    'update_business': update_business,
    'create_business': create_business
}
