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
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import List, Optional

from flask import jsonify
from marshmallow import ValidationError
from geofencing.db.models import UASZone
from geofencing.endpoints.schemas.reply import ReplySchema

__author__ = "EUROCONTROL (SWIM)"


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
        :param generic_reply:
        """
        self.generic_reply = generic_reply or GenericReply(RequestStatus.OK.value)


class UASZoneReply(Reply):

    def __init__(self, uas_zones: List[UASZone]):
        super().__init__()
        self.uas_zones = uas_zones


def handle_request(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                result = Reply(
                    generic_reply=GenericReply(
                        request_status=RequestStatus.NOK.value,
                        request_exception_description=str(e)
                    )
                )
            return schema().dump(result)
        return wrapper
    return decorator


def handle_flask_request_error(response):
    if response.status_code != 200:
        reply = Reply(generic_reply=GenericReply(
            request_status=RequestStatus.NOK.value,
            request_exception_description=response.json['detail']))
        data = ReplySchema().dump(reply)

        return jsonify(data)
