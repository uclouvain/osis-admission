# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_common.ddd.interface import BusinessException
from django.utils.translation import gettext_lazy as _


class ActiviteNonComplete(BusinessException):
    status_code = "FORMATION-1"

    def __init__(self, activite_id, *args, **kwargs):
        self.activite_id = activite_id
        message = _("This activity is not complete")
        super().__init__(message, **kwargs)


class ActiviteDejaSoumise(BusinessException):
    status_code = "FORMATION-2"

    def __init__(self, activite_id, *args, **kwargs):
        self.activite_id = activite_id
        message = _("This activity has been submitted")
        super().__init__(message, **kwargs)


class ActiviteNonTrouvee(BusinessException):
    status_code = "FORMATION-3"

    def __init__(self, *args, **kwargs):
        message = _("This activity could not be found")
        super().__init__(message, **kwargs)


class ActiviteDoitEtreNonSoumise(BusinessException):
    status_code = "FORMATION-4"

    def __init__(self, activite_id, *args, **kwargs):
        self.activite_id = activite_id
        message = _("This activity must be unsubmitted")
        super().__init__(message, **kwargs)


class ActiviteDoitEtreSoumise(BusinessException):
    status_code = "FORMATION-5"

    def __init__(self, activite_id=None, *args, **kwargs):
        self.activite_id = activite_id
        message = _("This activity must be submitted")
        super().__init__(message, **kwargs)
