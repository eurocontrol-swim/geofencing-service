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

from mongoengine import EmbeddedDocument, StringField, IntField, PolygonField, \
    ComplexDateTimeField, EmbeddedDocumentField, Document, ListField, EmbeddedDocumentListField, \
    DictField, ValidationError, ReferenceField, EmailField, URLField, BooleanField, DoesNotExist, \
    FloatField

from geofencing_service.db import AIRSPACE_VOLUME_UPPER_LIMIT, AIRSPACE_VOLUME_LOWER_LIMIT

__author__ = "EUROCONTROL (SWIM)"


class ChoiceType(enum.Enum):

    @classmethod
    def choices(cls) -> Tuple[Any]:
        return tuple(v.value for v in cls.__members__.values())


class CodeYesNoType(ChoiceType):
    YES = "YES"
    NO = "NO"


class CodeWeekDay(ChoiceType):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"
    ANY = "ANY"


class CodeZoneType(ChoiceType):
    COMMON = "COMMON"
    CUSTOMIZED = "CUSTOMIZED"


class CodeRestrictionType(ChoiceType):
    PROHIBITED = "PROHIBITED"
    REQ_AUTHORISATION = "REQ_AUTHORISATION"
    CONDITIONAL = "CONDITIONAL"
    NO_RESTRICTION = "NO_RESTRICTION"


class CodeUSpaceClassType(ChoiceType):
    EUROCONTROL = "EUROCONTROL"
    CORUS = "CORUS"


class CodeZoneReasonType(ChoiceType):
    AIR_TRAFFIC = "AIR_TRAFFIC"
    SENSITIVE = "SENSITIVE"
    PRIVACY = "PRIVACY"
    POPULATION = "POPULATION"
    NATURE = "NATURE"
    NOISE = "NOISE"
    FOREIGN_TERRITORY = "FOREIGN_TERRITORY"
    OTHER = "OTHER"


class CodeVerticalReferenceType(ChoiceType):
    AGL = "AGL"
    AMSL = "AMSL"


class UomDistance(ChoiceType):
    METERS = 'M'
    FEET = 'FT'


class CodeAuthorityRole(ChoiceType):
    AUTHORIZATION = "AUTHORIZATION"
    NOTIFICATION = "NOTIFICATION"
    INFORMATION = "INFORMATION"


class CircleField(EmbeddedDocument):
    type = StringField(default='Circle')
    center = ListField(FloatField())
    radius = FloatField()


class AirspaceVolume(EmbeddedDocument):
    uom_dimensions = StringField(choices=UomDistance.choices(), required=True)
    lower_limit = IntField(db_field='lowerLimit', default=AIRSPACE_VOLUME_LOWER_LIMIT)
    lower_vertical_reference = StringField(db_field='lowerVerticalReference',
                                           choices=CodeVerticalReferenceType.choices(),
                                           default=CodeVerticalReferenceType.AMSL.value)
    upper_limit = IntField(db_field='upperLimit', default=AIRSPACE_VOLUME_UPPER_LIMIT)
    upper_vertical_reference = StringField(db_field='upperVerticalReference',
                                           choices=CodeVerticalReferenceType.choices(),
                                           default=CodeVerticalReferenceType.AMSL.value)
    horizontal_projection = PolygonField(required=True)

    # helper field that holds geometry data in case of the horizontal projection if os  circle type
    circle = EmbeddedDocumentField(CircleField)


class DailyPeriod(EmbeddedDocument):
    day = StringField(choices=CodeWeekDay.choices())
    start_time = ComplexDateTimeField(db_field='startTime', required=True)
    end_time = ComplexDateTimeField(db_field='endTime', required=True)


class TimePeriod(EmbeddedDocument):
    permanent = StringField(choices=CodeYesNoType.choices(), required=True)
    start_date_time = ComplexDateTimeField(db_field='startDateTime', required=True)
    end_date_time = ComplexDateTimeField(db_field='endDateTime', required=True)
    schedule = EmbeddedDocumentListField(DailyPeriod)


class Authority(EmbeddedDocument):
    name = StringField(required=True, max_length=200)
    service = StringField(required=True, max_length=200)
    email = EmailField()
    contact_name = StringField(db_field='contactName', required=True, max_length=200)
    site_url = URLField(db_field='siteURL')
    phone = StringField(required=True, max_length=200)
    purpose = StringField(required=True, choices=CodeAuthorityRole.choices())
    interval_before = StringField(db_field='intervalBefore', required=True)

    def clean(self):
        if not (self.email or self.site_url or self.phone):
            raise ValidationError(f"One of email, site_url, phone must be defined.")


class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ('username',), 'unique': True}
        ]
    }


def _get_or_create_user(user: User) -> User:
    try:
        user = User.objects.get(username=user.username)
    except DoesNotExist:
        user.save()

    return user


class UASZone(Document):
    identifier = StringField(required=True, primary_key=True, max_length=7)
    country = StringField(min_length=3, max_length=3, required=True)
    name = StringField(max_length=200)
    type = StringField(choices=CodeZoneType.choices(), required=True)
    restriction = StringField(choices=CodeRestrictionType.choices(), max_length=200, required=True)
    restriction_conditions = ListField(StringField(), db_field='restrictionConditions')
    region = IntField(min_value=0, max_value=0xffff)
    reason = ListField(StringField(choices=CodeZoneReasonType.choices()), max_length=9)
    other_reason_info = StringField(max_length=30)
    regulation_exemption = StringField(choices=CodeYesNoType.choices())
    u_space_class = StringField(db_field='uSpaceClass', choices=CodeUSpaceClassType.choices(),
                                max_length=100)
    message = StringField(max_length=200)

    zone_authority = EmbeddedDocumentField(Authority, db_field='zoneAuthority', required=True)
    applicability = EmbeddedDocumentField(TimePeriod)
    geometry = EmbeddedDocumentListField(AirspaceVolume, required=True)
    extended_properties = DictField(db_field='extendedProperties')

    user = ReferenceField(User, required=True)

    def clean(self):
        if self.user is not None:
            self.user = _get_or_create_user(self.user)


class UASZonesFilter(EmbeddedDocument):
    airspace_volume = EmbeddedDocumentField(AirspaceVolume, db_field='airspaceVolume')
    regions = ListField()
    start_date_time = ComplexDateTimeField(db_field='startDateTime')
    end_date_time = ComplexDateTimeField(db_field='endDateTime')


class GeofencingSMSubscription(EmbeddedDocument):
    id = IntField(required=True)
    queue = StringField(required=True)
    topic_name = StringField(required=True)
    active = BooleanField(required=True)


class UASZonesSubscription(Document):
    id = StringField(required=True, primary_key=True)
    sm_subscription = EmbeddedDocumentField(GeofencingSMSubscription, required=True)
    uas_zones_filter = EmbeddedDocumentField(UASZonesFilter, required=True)
    user = ReferenceField(User, required=True)

    def clean(self):
        if self.user is not None:
            self.user = _get_or_create_user(self.user)
