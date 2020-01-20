"""
Copyright 2019 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open Source Initiative:
http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""
import json
import traceback
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import List, Optional, Type

from marshmallow import Schema
from swim_backend.errors import APIError

from geofencing_service.db.models import UASZone
from geofencing_service.endpoints.schemas.reply_schemas import ReplySchema

__author__ = "EUROCONTROL (SWIM)"

from geofencing_service.filters import UASZonesFilter


class RequestStatus(Enum):
    OK = "OK"
    NOK = "NOK"


class GenericReply:

    def __init__(self,
                 request_status: str,
                 request_exception_description: Optional[str] = None,
                 request_processed_timestamp: Optional[datetime] = None):
        """
        Encapsulates general information about the result of the respective request process
        :param request_status: can be OK or NOK
        :param request_exception_description:
        :param request_processed_timestamp:
        """
        self.request_status = request_status
        self.request_exception_description = request_exception_description
        self.request_processed_timestamp = request_processed_timestamp or datetime.now(timezone.utc)


class Reply:

    def __init__(self, generic_reply: Optional[GenericReply] = None):
        """
        The main reply object of the endpoints. All endpoints should inherit from here.
        :param generic_reply:
        """
        self.generic_reply = generic_reply or GenericReply(RequestStatus.OK.value)


class UASZoneFilterReply(Reply):

    def __init__(self, uas_zones: List[UASZone]):
        super().__init__()
        self.uas_zones = uas_zones


class UASZoneCreateReply(Reply):

    def __init__(self, uas_zone: UASZone):
        super().__init__()
        self.uas_zone = uas_zone


class SubscribeToUASZonesUpdatesReply(Reply):

    def __init__(self, subscription_id: str, publication_location: str):
        super().__init__()
        self.subscription_id = subscription_id
        self.publication_location = publication_location


class UASZoneSubscriptionReplyObject:

    def __init__(self, subscription_id: str, publication_location: str, active: bool, uas_zones_filter: UASZonesFilter):
        super().__init__()
        self.subscription_id = subscription_id
        self.publication_location = publication_location
        self.active = active
        self.uas_zones_filter = uas_zones_filter


class UASZoneSubscriptionReply(Reply):
    def __init__(self, uas_zone_subscription: UASZoneSubscriptionReplyObject):
        super().__init__()
        self.uas_zone_subscription = uas_zone_subscription


class UASZoneSubscriptionsReply(Reply):

    def __init__(self, uas_zone_subscriptions: List[UASZoneSubscriptionReplyObject]):
        super().__init__()
        self.uas_zone_subscriptions = uas_zone_subscriptions


def handle_response(schema: Type[Schema]):
    """
    Handles the response by dumping the returned object using the provided schema class and by handling any possible
    exception
    :param schema: the schema class
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result, status_code = func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                result = Reply(
                    generic_reply=GenericReply(
                        request_status=RequestStatus.NOK.value,
                        request_exception_description=str(e)
                    )
                )
                status_code = e.status if isinstance(e, APIError) else 500
            return schema().dump(result), status_code
        return wrapper
    return decorator


def handle_flask_request_error(response):
    """
    All the API related exceptions will be wrapped here in the Reply object
    :param response:
    :return:
    """
    if response.status_code != 200 and response.json and 'detail' in response.json:
        reply = Reply(generic_reply=GenericReply(
            request_status=RequestStatus.NOK.value,
            request_exception_description=response.json['detail']))

        response.data = json.dumps(ReplySchema().dump(reply))

    return response
