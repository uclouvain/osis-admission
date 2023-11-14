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
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_common.ddd.interface import BusinessException


class BusinessExceptionFormViewMixin:
    error_mapping = {}

    def __init__(self, *args, **kwargs):
        self._error_mapping = {exc.status_code: field for exc, field in self.error_mapping.items()}
        super().__init__(*args, **kwargs)

    def call_command(self, form):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.call_command(form=form)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                status_code = getattr(exception, 'status_code', None)
                form.add_error(self._error_mapping.get(status_code), exception.message)
            return self.form_invalid(form=form)
        except BusinessException as exception:
            messages.error(self.request, _("Some errors have been encountered."))
            status_code = getattr(exception, 'status_code', None)
            form.add_error(self._error_mapping.get(status_code), exception.message)
            return self.form_invalid(form=form)

        return super().form_valid(form=form)
