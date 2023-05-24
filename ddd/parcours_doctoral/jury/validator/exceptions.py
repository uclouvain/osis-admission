##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException


class PromoteurPresidentException(BusinessException):
    status_code = "JURY-1"

    def __init__(self, **kwargs):
        message = _("A promoter can not be president.")
        super().__init__(message, **kwargs)


class MembreNonTrouveDansJuryException(BusinessException):
    status_code = "JURY-3"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("The member was not found in the jury.")
        super().__init__(message, **kwargs)


class JuryNonTrouveException(BusinessException):
    status_code = "JURY-4"

    def __init__(self, **kwargs):
        message = _("No jury found.")
        super().__init__(message, **kwargs)


class PromoteurRetireException(BusinessException):
    status_code = "JURY-5"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("A promoter can not be removed from the jury.")
        super().__init__(message, **kwargs)


class PromoteurModifieException(BusinessException):
    status_code = "JURY-6"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("A promoter can not be updated from the jury.")
        super().__init__(message, **kwargs)


class NonDocteurSansJustificationException(BusinessException):
    status_code = "JURY-7"

    def __init__(self, **kwargs):
        message = _("A non doctor member must have a justification.")
        super().__init__(message, **kwargs)


class MembreExterneSansInstitutionException(BusinessException):
    status_code = "JURY-8"

    def __init__(self, **kwargs):
        message = _("An external member must have an institute.")
        super().__init__(message, **kwargs)


class MembreExterneSansPaysException(BusinessException):
    status_code = "JURY-9"

    def __init__(self, **kwargs):
        message = _("An external member must have a country.")
        super().__init__(message, **kwargs)


class MembreExterneSansNomException(BusinessException):
    status_code = "JURY-10"

    def __init__(self, **kwargs):
        message = _("An external member must have a last name.")
        super().__init__(message, **kwargs)


class MembreExterneSansPrenomException(BusinessException):
    status_code = "JURY-11"

    def __init__(self, **kwargs):
        message = _("An external member must have a first name.")
        super().__init__(message, **kwargs)


class MembreExterneSansTitreException(BusinessException):
    status_code = "JURY-12"

    def __init__(self, **kwargs):
        message = _("An external member must have a title.")
        super().__init__(message, **kwargs)


class MembreExterneSansGenreException(BusinessException):
    status_code = "JURY-13"

    def __init__(self, **kwargs):
        message = _("An external member must have a gender.")
        super().__init__(message, **kwargs)


class MembreExterneSansEmailException(BusinessException):
    status_code = "JURY-14"

    def __init__(self, **kwargs):
        message = _("An external member must have an email.")
        super().__init__(message, **kwargs)


class MembreDejaDansJuryException(BusinessException):
    status_code = "JURY-15"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("The member is already in the jury.")
        super().__init__(message, **kwargs)
