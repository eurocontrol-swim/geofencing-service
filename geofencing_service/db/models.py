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
from typing import Tuple, Any

from mongoengine import EmbeddedDocument, StringField, IntField, PolygonField, ComplexDateTimeField, \
    EmbeddedDocumentField, \
    Document, ListField, EmbeddedDocumentListField, DictField, ValidationError, ReferenceField, EmailField, URLField, \
    BooleanField, DoesNotExist

from geofencing_service.db import AIRSPACE_VOLUME_UPPER_LIMIT_IN_M, AIRSPACE_VOLUME_LOWER_LIMIT_IN_M

__author__ = "EUROCONTROL (SWIM)"


class Choice(enum.Enum):

    @classmethod
    def choices(cls) -> Tuple[Any]:
        return tuple(v.value for v in cls.__members__.values())


class CodeYesNoType(Choice):
    YES = "YES"
    NO = "NO"


class CodeWeekDay(Choice):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class CodeZoneType(Choice):
    COMMON = "COMMON"
    CUSTOMIZED = "CUSTOMIZED"


class CodeRestrictionType(Choice):
    PROHIBITED = "PROHIBITED"
    REQ_AUTHORISATION = "REQ_AUTHORISATION"
    CONDITIONAL = "CONDITIONAL"
    NO_RESTRICTION = "NO_RESTRICTION"


class CodeUSpaceClassType(Choice):
    EUROCONTROL = "EUROCONTROL"
    CORUS = "CORUS"


class CodeZoneReasonType(Choice):
    AIR_TRAFFIC = "AIR_TRAFFIC"
    SENSITIVE = "SENSITIVE"
    PRIVACY = "PRIVACY"
    POPULATION = "POPULATION"
    NATURE = "NATURE"
    NOISE = "NOISE"
    FOREIGN_TERRITORY = "FOREIGN_TERRITORY"
    OTHER = "OTHER"


class CodeVerticalReferenceType(Choice):
    AGL = "AGL"
    AMSL = "AMSL"
    WGS84 = "WGS84"


class AirspaceVolume(EmbeddedDocument):
    lower_limit_in_m = IntField(db_field='lowerLimit', default=AIRSPACE_VOLUME_LOWER_LIMIT_IN_M)
    lower_vertical_reference = StringField(db_field='lowerVerticalReference',
                                           choices=CodeVerticalReferenceType.choices())
    upper_limit_in_m = IntField(db_field='upperLimit', default=AIRSPACE_VOLUME_UPPER_LIMIT_IN_M)
    upper_vertical_reference = StringField(db_field='upperVerticalReference',
                                           choices=CodeVerticalReferenceType.choices())
    polygon = PolygonField(required=True)


class DailySchedule(EmbeddedDocument):
    day = StringField(choices=CodeWeekDay.choices())
    start_time = ComplexDateTimeField(db_field='startTime', required=True)
    end_time = ComplexDateTimeField(db_field='endTime', required=True)


class ApplicableTimePeriod(EmbeddedDocument):
    permanent = StringField(choices=CodeYesNoType.choices())
    start_date_time = ComplexDateTimeField(db_field='startDateTime', required=True)
    end_date_time = ComplexDateTimeField(db_field='endDateTime', required=True)
    daily_schedule = EmbeddedDocumentListField(DailySchedule, db_field='dailySchedule')


class AuthorityEntity(Document):
    name = StringField(required=True, unique=True)
    contact_name = StringField(db_field='contactName', required=True)
    service = StringField(required=True)
    email = EmailField()
    site_url = URLField(db_field='siteURL')
    phone = StringField(required=True)

    def clean(self):
        if not (self.email or self.site_url or self.phone):
            raise ValidationError(f"One of email, site_url, phone must be defined.")


def _save_authority_entity_if_not_exists(authority_entity: AuthorityEntity) -> AuthorityEntity:
    try:
        return AuthorityEntity.objects.get(name=authority_entity.name)
    except DoesNotExist:
        authority_entity.save()
        return authority_entity


class NotificationRequirement(EmbeddedDocument):
    authority = ReferenceField(AuthorityEntity, required=True)
    interval_before = StringField(db_field='intervalBefore', required=True)


class AuthorizationRequirement(EmbeddedDocument):
    authority = ReferenceField(AuthorityEntity, required=True)


class Authority(EmbeddedDocument):
    requires_notification_to = EmbeddedDocumentField(NotificationRequirement, db_field="requiresNotificationTo")
    requires_authorization_from = EmbeddedDocumentField(AuthorizationRequirement, db_field="requiresAuthorisationFrom")


class DataSource(EmbeddedDocument):
    author = StringField(max_length=200)
    creation_date_time = ComplexDateTimeField(db_field='creationDateTime', required=True)
    update_date_time = ComplexDateTimeField(db_field='endDateTime')


class UASZone(Document):
    identifier = StringField(required=True, primary_key=True, max_length=7)
    name = StringField(required=True, max_length=200)
    type = StringField(choices=CodeZoneType.choices(), required=True)
    restriction = StringField(choices=CodeRestrictionType.choices(), max_length=200, required=True)
    restriction_conditions = ListField(StringField(), db_field='restrictionConditions')
    region = IntField(min_value=0, max_value=0xffff)
    data_capture_prohibition = StringField(db_field='dataCaptureProhibition',
                                           choices=CodeYesNoType.choices(),
                                           required=True)
    u_space_class = StringField(db_field='uSpaceClass', choices=CodeUSpaceClassType.choices(), max_length=200)
    message = StringField(max_length=200)
    reason = ListField(StringField(choices=CodeZoneReasonType.choices()))
    country = StringField(min_length=3, max_length=3, required=True)

    airspace_volume = EmbeddedDocumentField(AirspaceVolume, db_field='airspaceVolume', required=True)
    applicable_time_period = EmbeddedDocumentField(ApplicableTimePeriod, db_field='applicableTimePeriod')
    authority = EmbeddedDocumentField(Authority)
    data_source = EmbeddedDocumentField(DataSource, db_field='dataSource')
    extended_properties = DictField(db_field='extendedProperties')

    def clean(self):
        if self.data_source.update_date_time is None:
            self.data_source.update_date_time = self.data_source.creation_date_time

        # save reference documents beforehand
        self.notification_authority = _save_authority_entity_if_not_exists(self.notification_authority)
        self.authorization_authority = _save_authority_entity_if_not_exists(self.authorization_authority)

    def _has_notification_authority(self):
        return self.authority and \
                self.authority.requires_notification_to and \
                self.authority.requires_notification_to.authority

    def _has_authorization_authority(self):
        return self.authority and \
                self.authority.requires_authorization_from and \
                self.authority.requires_authorization_from.authority

    @property
    def notification_authority(self):
        if self._has_notification_authority():
            return self.authority.requires_notification_to.authority

    @notification_authority.setter
    def notification_authority(self, authority_entity: AuthorityEntity):
        if self._has_notification_authority():
            self.authority.requires_notification_to.authority = authority_entity

    @property
    def authorization_authority(self):
        if self._has_authorization_authority():
            return self.authority.requires_authorization_from.authority

    @authorization_authority.setter
    def authorization_authority(self, authority_entity: AuthorityEntity):
        if self._has_authorization_authority():
            self.authority.requires_authorization_from.authority = authority_entity


class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ('username',), 'unique': True}
        ]
    }


class UASZonesSubscription(Document):
    id = StringField(required=True, primary_key=True)
    publication_location = StringField(required=True, db_field='publicationLocation')
    active = BooleanField(required=True)
    uas_zones_filter = DictField(required=True)
    topic_name = StringField(required=True)
