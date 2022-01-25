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

try:
    from .doctorate import DoctorateAdmission
    from .actor import SupervisionActor
    from .enums.admission_type import AdmissionType
    from .entity_proxy import EntityProxy

    __all__ = [
        "DoctorateAdmission",
        "AdmissionType",
        "SupervisionActor",
        "EntityProxy",
    ]

except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
