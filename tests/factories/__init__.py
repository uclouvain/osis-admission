# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import string
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyText

from .doctorate import DoctorateAdmissionFactory

__all__ = [
    "DoctorateAdmissionFactory",
    "WriteTokenFactory",
]


class PdfUploadFactory:
    def __init__(self, **kwargs):
        self.uuid = uuid4()
        self.file = factory.django.FileField(data=b'hello world', filename='the_file.pdf')
        self.size = 1024
        self.mimetype = 'application/pdf'
        self.metadata = {
            'hash': 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9',
            'name': 'the_file.pdf',
        }


class WriteTokenFactory:
    def __init__(self, **kwargs):
        self.token = FuzzyText(length=154, chars=string.ascii_letters + string.digits + ':-').fuzz()
        self.upload = PdfUploadFactory()
        self.access = "WRITE"
