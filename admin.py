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

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


from admission.auth.roles.adre import Adre
from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.candidate import Candidate
from admission.auth.roles.cdd_manager import CddManager
from admission.auth.roles.jury_secretary import JurySecretary
from admission.auth.roles.promoter import Promoter
from admission.auth.roles.sceb import Sceb
from admission.auth.roles.sic_director import SicDirector
from admission.auth.roles.sic_manager import SicManager
from admission.contrib.models import CddMailTemplate, DoctorateAdmission
from osis_mail_template.admin import MailTemplateAdmin

from osis_profile.models.curriculum import CurriculumYear, Experience
from osis_role.contrib.admin import RoleModelAdmin

# ##############################################################################
# Models


class DoctorateAdmissionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['doctorate', 'thesis_institute']
    list_display = ['reference', 'candidate_fmt', 'doctorate', 'type', 'status']
    list_filter = ['status', 'type']
    list_select_related = ['candidate', 'doctorate']
    readonly_fields = [
        "project_document",
        "gantt_graph",
        "program_proposition",
        "additional_training_project",
        "recommendation_letters",
        "cotutelle_opening_request",
        "cotutelle_convention",
        "cotutelle_other_documents",
        "detailed_status",
    ]

    def candidate_fmt(self, obj):
        return "{} ({global_id})".format(obj.candidate, global_id=obj.candidate.global_id)

    candidate_fmt.short_description = _("Candidate")


class ExperienceInlineAdmin(admin.TabularInline):
    model = Experience


class CurriculumYearAdmin(admin.ModelAdmin):
    inlines = [ExperienceInlineAdmin]
    autocomplete_fields = ["person"]


class CddMailTemplateAdmin(MailTemplateAdmin):
    list_display = ('name', 'identifier', 'language', 'cdd')
    search_fields = [
        'cdd__acronym',
        'idenfier',
    ]
    list_filter = [
        'cdd',
        'language',
        'identifier',
    ]


admin.site.register(DoctorateAdmission, DoctorateAdmissionAdmin)
admin.site.register(CurriculumYear, CurriculumYearAdmin)
admin.site.register(CddMailTemplate, CddMailTemplateAdmin)


# ##############################################################################
# Roles


class ExternalCommitteeMemberAdmin(RoleModelAdmin):
    list_display = ('person', 'is_external', 'title', 'institute', 'city', 'country')
    list_filter = ['is_external']
    list_select_related = ['person', 'country']


class CDDRoleModelAdmin(RoleModelAdmin):
    list_display = ('person', 'entity')
    search_fields = [
        'person__first_name',
        'person__last_name',
        'entity__entityversion__acronym',
    ]


admin.site.register(Promoter, ExternalCommitteeMemberAdmin)
admin.site.register(CommitteeMember, ExternalCommitteeMemberAdmin)
admin.site.register(SicManager, RoleModelAdmin)
admin.site.register(SicDirector, RoleModelAdmin)
admin.site.register(Adre, RoleModelAdmin)
admin.site.register(Candidate, RoleModelAdmin)
admin.site.register(JurySecretary, RoleModelAdmin)
admin.site.register(Sceb, RoleModelAdmin)
admin.site.register(CddManager, CDDRoleModelAdmin)
