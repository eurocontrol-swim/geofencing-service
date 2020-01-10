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
from datetime import datetime, timezone

import dateutil.parser

__author__ = "EUROCONTROL (SWIM)"


def time_str_from_datetime_str(date_string: str) -> str:
    """
    Extracts the time parts of a datetime.

    Example:
        2019-12-03T09:00:00.12345 will be converted to:
        09:00:00.12345

    :param date_string:
    :return:
    """
    return date_string.split('T')[1]


def datetime_str_from_time_str(time_str: str) -> str:
    """
    Applies a dummy date on a time string for further storage as datetime

    :param time_str:
    :return:
    """
    return f"2000-01-01T{time_str}"


def make_datetime_string_aware(dt: str) -> str:
    """
    Applies UTC timezone on a datetime string,

    :param dt:
    :return:
    """
    return make_datetime_aware(dateutil.parser.parse(dt)).isoformat()


def make_datetime_aware(dt: datetime) -> datetime:
    """
    Applies UTC timezone of a datetime

    :param dt:
    :return:
    """
    return dt.replace(tzinfo=timezone.utc)


