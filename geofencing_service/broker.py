"""
Copyright 2020 EUROCONTROL
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

__author__ = "EUROCONTROL (SWIM)"

import enum
import logging
from typing import Optional, Any

import proton

from geofencing_service.db.models import UASZone
from geofencing_service.db.uas_zones import get_uas_zones as db_get_uas_zones
from geofencing_service.endpoints.schemas.db_schemas import UASZoneSchema
from geofencing_service.filters import UASZonesFilter

_logger = logging.getLogger(__name__)


class UASZonesUpdatesMessageType(enum.Enum):
    INITIAL = 'INITIAL'
    UAS_ZONE_CREATION = 'UAS_ZONE_CREATION'
    UAS_ZONE_DELETION = 'UAS_ZONE_DELETION'


class UASZonesUpdatesMessageProducerContext:
    def __init__(self, message_type: UASZonesUpdatesMessageType, data: Any):
        self.message_type = message_type
        self.data = data


def uas_zones_updates_message_producer(context: UASZonesUpdatesMessageProducerContext) -> proton.Message:
    """
    The message producer (UASZones retrieval) that will be called every time the topic is triggered for publishing.

    :param context: Mandatory parameter required by `swim-pubsub`. Here it contains the UASZone filtering criteria of
                    the subscription
    :return:
    """
    if context.message_type == UASZonesUpdatesMessageType.INITIAL:
        if not isinstance(context.data, UASZonesFilter):
            raise ValueError(f"Data for message_type INITIAL should be UASZonesFilter")

        uas_zones = db_get_uas_zones(uas_zones_filter=context.data)
        message_body = {
            'uas_zones': [UASZoneSchema().dump(uas_zone) for uas_zone in uas_zones]
        }
    elif context.message_type == UASZonesUpdatesMessageType.UAS_ZONE_CREATION:
        if not isinstance(context.data, UASZone):
            raise ValueError(f"Data for message_type UAS_ZONE_CREATION should be UASZone")

        message_body = {
            'uas_zone': UASZoneSchema().dump(context.data)
        }
    elif context.message_type == UASZonesUpdatesMessageType.UAS_ZONE_DELETION:
        if not isinstance(context.data, str):
            raise ValueError(f"Data for message_type UAS_ZONE_DELETION should be str")

        message_body = {
            'uas_zone_identifier': context.data
        }
    else:
        raise ValueError('Invalid message_type')

    message_body['message_type'] = context.message_type.value

    return proton.Message(body=message_body, content_type="application/json")
