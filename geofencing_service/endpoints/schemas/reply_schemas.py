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
from marshmallow import Schema
from marshmallow.fields import Nested, String, DateTime, Boolean

from geofencing_service.endpoints.schemas.db_schemas import UASZoneSchema, UASZonesFilterSchema

__author__ = "EUROCONTROL (SWIM)"


class GenericReplySchema(Schema):
    request_status = String(data_key="RequestStatus")
    request_exception_description = String(data_key="RequestExceptionDescription")
    request_processed_timestamp = DateTime(data_key="RequestProcessedTimestamp")


class ReplySchema(Schema):
    generic_reply = Nested(GenericReplySchema, required=True, data_key="genericReply")


class UASZonesFilterReplySchema(ReplySchema):
    uas_zones = Nested(UASZoneSchema, many=True, data_key="UASZoneList")


class UASZoneCreateReplySchema(ReplySchema):
    uas_zone = Nested(UASZoneSchema, data_key="UASZone")


class SubscribeToUASZonesUpdatesReplySchema(ReplySchema):
    subscription_id = String(data_key="subscriptionID")
    publication_location = String(data_key="publicationLocation")


class UASZoneSubscriptionReplyObjectSchema(ReplySchema):
    subscription_id = String(data_key="subscriptionID")
    publication_location = String(data_key="publicationLocation")
    active = Boolean()
    uas_zones_filter = Nested(UASZonesFilterSchema, data_key='UASZonesFilter')


class UASZoneSubscriptionReplySchema(ReplySchema):
    uas_zone_subscription = Nested(UASZoneSubscriptionReplyObjectSchema,
                                   data_key='subscription')


class UASZoneSubscriptionsReplySchema(ReplySchema):
    uas_zone_subscriptions = Nested(UASZoneSubscriptionReplyObjectSchema,
                                    many=True,
                                    data_key='subscriptions')
