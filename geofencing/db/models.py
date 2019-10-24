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
import enum

from mongoengine import EmbeddedDocument, StringField, IntField, PolygonField, DateTimeField, EmbeddedDocumentField, \
    Document, ListField, EmbeddedDocumentListField

__author__ = "EUROCONTROL (SWIM)"


class YesNoChoice(enum.Enum):
    YES = "YES"
    NO = "NO"


class AirspaceVolume(EmbeddedDocument):

    id = StringField(required=True, unique=True)
    lower_limit_in_m = IntField()
    lower_vertical_reference = StringField()
    upper_limit_in_m = IntField()
    upper_vertical_reference = StringField()
    polygon = PolygonField(required=True)


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class DailySchedule(EmbeddedDocument):

    id = StringField(required=True, unique=True)

    day = StringField(choices=(day.name for day in Day))
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)


class ApplicableTimePeriod(EmbeddedDocument):

    id = StringField(required=True, unique=True)
    permanent = StringField(choices=(e.name for e in YesNoChoice))
    start_date_time = DateTimeField(required=True)
    end_date_time = DateTimeField(required=True)
    daily_schedule = EmbeddedDocumentListField(DailySchedule)


class Authority(EmbeddedDocument):

    id = StringField(required=True, unique=True)

    name = StringField(required=True)
    contact_name = StringField()
    service = StringField()

    # at  least  one  of  the  following  shall  be  specified
    email = StringField()
    site_url = StringField()
    phone = StringField()


class Country(EmbeddedDocument):

    id = StringField(required=True, unique=True)
    name = StringField(required=True)
    iso_code3 = StringField(required=True)


class UASType(enum.Enum):
    COMMON = "COMMON"
    CUSTOMIZED = "CUSTOMIZED"


class UASRestriction(enum.Enum):
    PROHIBITED = "PROHIBITED"
    REQ_AUTHORISATION = "REQ_AUTHORISATION"
    CONDITIONAL = "CONDITIONAL"
    NO_RESTRICTION = "NO_RESTRICTION"


class USpaceClass(enum.Enum):
    EUROCONTROL = "EUROCONTROL"
    CORUS = "CORUS"


class NotificationRequirement(EmbeddedDocument):

    id = StringField(required=True, unique=True)
    authority = EmbeddedDocumentField(Authority, required=True)
    interval_before = StringField(required=True)


class UASZoneReason(enum.Enum):
    AIR_TRAFFIC = "AIR_TRAFFIC"
    SENSITIVE = "SENSITIVE"
    PRIVACY = "PRIVACY"
    POPULATION = "POPULATION"
    NATURE = "NATURE"
    NOISE = "NOISE"
    FOREIGN_TERRITORY = "FOREIGN_TERRITORY"
    OTHER = "OTHER"


class UASZone(Document):

    identifier = StringField(required=True, unique=True)

    name = StringField(required=True)
    type = StringField(choices=(t.name for t in UASType))
    restriction = StringField(choices=(r.name for r in UASRestriction))
    # region = IntField()
    data_capture_prohibition = StringField(choices=(e.name for e in YesNoChoice))
    u_space_class = StringField(choices=(s.name for s in USpaceClass))
    message = StringField()
    creation_date_time = DateTimeField(required=True)
    update_date_time = DateTimeField()

    reason = ListField(StringField(choices=(r.name for r in UASZoneReason)))
    country = EmbeddedDocumentField(Country)
    airspace_volume = EmbeddedDocumentField(AirspaceVolume, required=True)
    notification_requirement = EmbeddedDocumentField(NotificationRequirement)
    authorization_requirement = EmbeddedDocumentField(Authority)
    applicable_time_period = EmbeddedDocumentField(ApplicableTimePeriod)
    # author = EmbeddedDocumentField(Authority)
