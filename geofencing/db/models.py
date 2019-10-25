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
    Document, ListField, EmbeddedDocumentListField, DictField, ValidationError, ReferenceField

__author__ = "EUROCONTROL (SWIM)"


class YesNoChoice(enum.Enum):
    YES = "YES"
    NO = "NO"


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


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


class UASZoneReason(enum.Enum):
    AIR_TRAFFIC = "AIR_TRAFFIC"
    SENSITIVE = "SENSITIVE"
    PRIVACY = "PRIVACY"
    POPULATION = "POPULATION"
    NATURE = "NATURE"
    NOISE = "NOISE"
    FOREIGN_TERRITORY = "FOREIGN_TERRITORY"
    OTHER = "OTHER"


class AirspaceVolume(EmbeddedDocument):
    lower_limit_in_m = IntField(db_field='lowerLimit')
    lower_vertical_reference = StringField(db_field='lowerVerticalReference')
    upper_limit_in_m = IntField(db_field='upperLimit')
    upper_vertical_reference = StringField(db_field='upperVerticalReference')
    polygon = PolygonField(required=True)


class DailySchedule(EmbeddedDocument):
    day = StringField(choices=tuple(e.value for e in Day))
    start_time = DateTimeField(db_field='startTime', required=True)
    end_time = DateTimeField(db_field='endTime', required=True)


class ApplicableTimePeriod(EmbeddedDocument):
    permanent = StringField(choices=tuple(e.value for e in YesNoChoice))
    start_date_time = DateTimeField(db_field='startDateTime', required=True)
    end_date_time = DateTimeField(db_field='endDateTime', required=True)
    daily_schedule = EmbeddedDocumentListField(DailySchedule, db_field='dailySchedule')


class Authority(Document):
    authority_id = StringField(primary_key=True)
    name = StringField(required=True)
    contact_name = StringField(db_field='contactName')
    service = StringField()
    email = StringField()
    site_url = StringField(db_field='siteUrl')
    phone = StringField()

    def clean(self):
        if not (self.email or self.site_url or self.phone):
            raise ValidationError(f"One of email, site_url, phone must be defined.")


class NotificationRequirement(EmbeddedDocument):
    authority = ReferenceField(Authority, required=True)
    interval_before = StringField(db_field='intervalBefore', required=True)


class DataSource(EmbeddedDocument):
    # author = ReferenceField(Authority, required=True)
    creation_date_time = DateTimeField(db_field='creationDateTime', required=True)
    update_date_time = DateTimeField(db_field='endDateTime', )


class UASZone(Document):
    identifier = StringField(required=True, primary_key=True)
    name = StringField(required=True)
    type = StringField(choices=tuple(e.value for e in UASType))
    restriction = StringField(choices=tuple(e.value for e in UASRestriction))
    # region = IntField()
    data_capture_prohibition = StringField(db_field='dataCaptureProhibition', choices=tuple(e.value for e in YesNoChoice))
    u_space_class = StringField(db_field='uSpaceClass', choices=tuple(e.value for e in USpaceClass))
    message = StringField()

    reason = ListField(StringField(choices=tuple(e.value for e in UASZoneReason)))
    country = StringField()
    airspace_volume = EmbeddedDocumentField(AirspaceVolume, db_field='airspaceVolume', required=True)
    notification_requirement = EmbeddedDocumentField(NotificationRequirement, db_field='notificationRequirement')
    authorization_requirement = ReferenceField(Authority, db_field='authorizationRequirement')
    applicable_time_period = EmbeddedDocumentField(ApplicableTimePeriod, db_field='applicableTimePeriod')
    data_source = EmbeddedDocumentField(DataSource, db_field='dataSource')
    extended_properties = DictField(db_field='extendedProperties')
