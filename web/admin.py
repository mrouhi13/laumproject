from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from templated_mail.mail import BaseEmailMessage

from .helpers import get_active_language
from .models import User, Group, Page, Tag, Report
from .persian_editors import PersianEditors

admin.site.site_header = _('Laum Project administration')
admin.site.site_title = _('Laum Project administration')
admin.site.index_title = _('Dashboard')


@admin.register(User)
class UserAdmin(UserAdmin):
    date_hierarchy = 'date_joined'
    fieldsets = (
        (None, {'fields': ['email', 'password']}),
        (_('Personal info'), {'fields': ['first_name', 'last_name']}),
        (_('Permissions'), {
            'fields': ['is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'],
        }),
        (_('Important dates'), {'fields': ['last_login', 'date_joined']}),
    )
    add_fieldsets = (
        (None, {
            'classes': ['wide'],
            'fields': ['email', 'password1', 'password2'],
        }),
    )
    list_display = ['email', 'first_name', 'last_name', 'is_staff']
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['email']
    readonly_fields = ['last_login', 'date_joined']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    readonly_fields = ['gid', 'jalali_updated_on', 'jalali_created_on']
    fieldsets = [
        [_('Main info'),
         {'fields': ['gid']}],
        [_('Important dates'), {'fields': ['jalali_updated_on',
                                           'jalali_created_on']}]]
    list_display = ['gid', 'jalali_updated_on',
                    'jalali_created_on']
    list_filter = ['updated_on', 'created_on']
    search_fields = ['gid']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    readonly_fields = ['links', 'image_tag', 'jalali_updated_on',
                       'jalali_created_on']
    fieldsets = [
        [_('Main info'),
         {'fields': ['group', 'links', 'title', 'subtitle',
                     'content', 'event', 'image', 'image_tag',
                     'image_caption']}],
        [_('Further info'), {'fields': ['tags', 'reference', 'website',
                                        'author', 'is_active']}],
        [_('Important dates'), {'fields': ['jalali_updated_on',
                                           'jalali_created_on']}]]
    list_display = ['title', 'author', 'is_active', 'jalali_updated_on',
                    'jalali_created_on']
    list_filter = ['is_active', 'updated_on', 'created_on']
    search_fields = ['group', 'pid', 'title', 'content', 'event',
                     'image_caption', 'tags__name', 'tags__keyword', 'website',
                     'author', 'reference']
    filter_horizontal = ['tags']

    def links(self, obj):
        page_link = reverse(f'web:page-detail', args=[obj.pid])
        reports_link = f'{reverse("admin:web_report_changelist")}?q={obj.pid}'
        reports = _('reports')
        return mark_safe(
            f'<a href="{page_link}" target="_blank">{obj.pid}</a> /'
            f' <a href="{reports_link}" target="_blank">{reports}</a>')

    links.short_description = _('public ID')

    def image_tag(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" width=150 height=150>')

    image_tag.short_description = _('image preview')

    def get_queryset(self, request):
        return Page.objects.filter(language=get_active_language())

    def save_model(self, request, obj, form, change):
        editor = PersianEditors(['space', 'number',
                                 'arabic', 'punctuation_marks'])

        obj.title = editor.run(obj.title)
        obj.subtitle = editor.run(obj.subtitle)
        obj.content = editor.run(obj.content)
        obj.event = editor.run(obj.event)
        obj.image_caption = editor.run(obj.image_caption)

        super().save_model(request, obj, form, change)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    fieldsets = [
        [_('Main info'), {
            'fields': ['view_page', 'send_email', 'rid', 'body',
                       'description', 'status']}],
        [_('Important dates'),
         {'fields': ['jalali_updated_on', 'jalali_created_on']}]]
    list_display = ['page', 'reporter', 'status', 'jalali_updated_on',
                    'jalali_created_on', 'rid']
    list_filter = ['status', 'updated_on', 'created_on']
    search_fields = ['page__pid', 'rid', 'body', 'reporter', 'rid',
                     'description']

    def view_page(self, obj):
        link_to_admin_view = reverse(f'admin:web_page_change',
                                     args=[obj.page.pk])
        link_to_site = reverse(f'web:page-detail', args=[obj.page.pid])
        view_page = _('view page')
        return mark_safe(
            f'<a href="{link_to_admin_view}" target="_blank">{obj.page}</a> / '
            f'<a href="{link_to_site}" target="_blank">{view_page}</a>')

    view_page.short_description = _('page')

    def send_email(self, obj):
        return mark_safe(f'<a href="mailto:{obj.reporter}">{obj.reporter}</a>')

    send_email.short_description = _('reporter email')

    def get_readonly_fields(self, request, obj=None):
        self.readonly_fields = ['view_page', 'body', 'rid', 'send_email',
                                'jalali_updated_on', 'jalali_created_on']
        if obj and not obj.status == Report.STATUS_IS_PENDING:
            self.readonly_fields.extend(['description', 'status'])
        return self.readonly_fields

    def get_queryset(self, request):
        return Report.objects.filter(language=get_active_language())

    def save_model(self, request, obj, form, change):
        is_first_change = False

        if 'status' not in self.readonly_fields and \
                not obj.status == Report.STATUS_IS_PENDING:
            is_first_change = True

        if is_first_change and not form.cleaned_data['description']:
            obj.description = _('-')

        editor = PersianEditors(
            ['space', 'number', 'arabic', 'punctuation_marks'])
        obj.description = editor.run(obj.description)

        editor.set_editors(['space'])
        editor.escape_return = False
        obj.body = editor.run(obj.body)

        super().save_model(request, obj, form, change)

        if is_first_change:  # Send email notification to user
            context = {'report': obj}
            email_template = 'emails/report_result.html'
            message = BaseEmailMessage(request, context, email_template)
            message.send([obj.reporter])

    def has_add_permission(self, request):
        return False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    readonly_fields = ['jalali_updated_on', 'jalali_created_on']
    fieldsets = [
        (_('Main info'), {'fields': ['name', 'keyword', 'is_active']}),
        (_('Important dates'), {'fields': ['jalali_updated_on',
                                           'jalali_created_on']})]
    list_display = ['name', 'keyword', 'is_active', 'jalali_updated_on',
                    'jalali_created_on']
    list_filter = ['is_active', 'updated_on', 'created_on']
    search_fields = ['name', 'keyword']
    prepopulated_fields = {'keyword': ['name']}

    def get_queryset(self, request):
        return Tag.objects.filter(language=get_active_language())
