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
import logging
from typing import Tuple

from flask import request
from marshmallow import ValidationError
from swim_backend.errors import BadRequestError, NotFoundError

from geofencing.db.subscriptions import update_uas_zones_subscription as db_update_uas_zones_subscription, \
    get_uas_zones_subscription_by_id, delete_uas_zones_subscription as db_delete_uas_zones_subscription
from geofencing.endpoints.reply import handle_response, SubscribeToUASZonesUpdatesReply, Reply, GenericReply, \
    RequestStatus
from geofencing.endpoints.schemas.db_schemas import SubscriptionSchema
from geofencing.endpoints.schemas.reply_schemas import SubscribeToUASZonesUpdatesReplySchema, ReplySchema
from geofencing.endpoints.schemas.filters_schemas import UASZonesFilterSchema
from geofencing.events import events

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


@handle_response(SubscribeToUASZonesUpdatesReplySchema)
def create_subscription_to_uas_zones_updates() -> Tuple[SubscribeToUASZonesUpdatesReply, int]:
    """

    :return:
    """
    try:
        uas_zones_filter = UASZonesFilterSchema().load(request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    uas_zones_subscription = events.create_uas_zones_subscription_event(uas_zones_filter=uas_zones_filter)

    return SubscribeToUASZonesUpdatesReply(uas_zones_subscription.id, uas_zones_subscription.publication_location), 201


@handle_response(ReplySchema)
def update_subscription_to_uas_zones_updates(subscription_id: str) -> Tuple[Reply, int]:
    """

    :param subscription_id:
    :return:
    """
    subscription = get_uas_zones_subscription_by_id(subscription_id)

    if subscription is None:
        raise NotFoundError(f"Subscription with id {subscription_id} does not exist")

    try:
        updated_subscription_dict = SubscriptionSchema().load(data=request.get_json())
    except ValidationError as e:
        raise BadRequestError(str(e))

    subscription.active = updated_subscription_dict['active']

    db_update_uas_zones_subscription(subscription)

    return Reply(generic_reply=GenericReply(request_status=RequestStatus.OK.value)), 200


@handle_response(ReplySchema)
def delete_subscription_to_uas_zones_updates(subscription_id: str) -> Tuple[Reply, int]:
    """

    :param subscription_id:
    :return:
    """
    subscription = get_uas_zones_subscription_by_id(subscription_id)

    if subscription is None:
        raise NotFoundError(f"Subscription with id {subscription_id} does not exist")

    db_delete_uas_zones_subscription(subscription)

    return Reply(generic_reply=GenericReply(request_status=RequestStatus.OK.value)), 204
