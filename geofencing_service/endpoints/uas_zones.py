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
from typing import Tuple

from flask import request
from marshmallow import ValidationError
from swim_backend.errors import BadRequestError, NotFoundError

from geofencing_service.db.uas_zones import get_uas_zones as db_get_uas_zones, get_uas_zones_by_identifier
from geofencing_service.endpoints.reply import UASZoneFilterReply, handle_response, UASZoneCreateReply, Reply, \
    GenericReply, RequestStatus
from geofencing_service.endpoints.schemas.db_schemas import UASZoneSchema
from geofencing_service.endpoints.schemas.filters_schemas import UASZonesFilterSchema
from geofencing_service.endpoints.schemas.reply_schemas import UASZonesFilterReplySchema, UASZoneCreateReplySchema, \
    ReplySchema
from geofencing_service.events.events import create_uas_zone_event, delete_uas_zone_event

__author__ = "EUROCONTROL (SWIM)"


@handle_response(UASZonesFilterReplySchema)
def filter_uas_zones() -> Tuple[UASZoneFilterReply, int]:
    """
    POST /uas_zones/filter

    Expected HTTP codes: 200, 400, 401, 500

    :return:
    """
    try:
        uas_zones_filter = UASZonesFilterSchema().load(request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    uas_zones = db_get_uas_zones(uas_zones_filter)

    return UASZoneFilterReply(uas_zones=uas_zones), 200


@handle_response(UASZoneCreateReplySchema)
def create_uas_zone() -> Tuple[UASZoneCreateReply, int]:
    """
    POST /uas_zones/

    Expected HTTP codes: 201, 400, 401, 500
    :return:
    """
    try:
        uas_zone = UASZoneSchema().load(request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    db_uas_zone = create_uas_zone_event(uas_zone=uas_zone)

    return UASZoneCreateReply(uas_zone=db_uas_zone), 201


@handle_response(ReplySchema)
def delete_uas_zone(uas_zone_identifier: str) -> Tuple[Reply, int]:
    """
    DELETE /uas_zones/{uas_zone_identifier}

    Expected HTTP codes: 204, 400, 401, 404, 500

    :param uas_zone_identifier:
    :return:
    """
    uas_zone = get_uas_zones_by_identifier(uas_zone_identifier)

    if uas_zone is None:
        raise NotFoundError(f"UASZone with identifier '{uas_zone_identifier}' does not exist")

    delete_uas_zone_event(uas_zone=uas_zone)

    return Reply(generic_reply=GenericReply(request_status=RequestStatus.OK.value)), 204
