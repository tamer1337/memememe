from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserPoints, PointHistory, ChatMessage

User = get_user_model()

# Фильтры для админки
class IsUpgradedFilter(admin.SimpleListFilter):
    title = 'Премиум статус'
    parameter_name = 'is_upgraded'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_upgraded=True)
        if self.value() == 'no':
            return queryset.filter(is_upgraded=False)

class PointsRangeFilter(admin.SimpleListFilter):
    title = 'Диапазон баллов'
    parameter_name = 'points_range'

    def lookups(self, request, model_admin):
        return (
            ('0', '0 баллов'),
            ('1-100', '1-100'),
            ('101-1000', '101-1000'),
            ('1001+', '1001+'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(points=0)
        if self.value() == '1-100':
            return queryset.filter(points__range=(1, 100))
        if self.value() == '101-1000':
            return queryset.filter(points__range=(101, 1000))
        if self.value() == '1001+':
            return queryset.filter(points__gte=1001)

# Action для админки
def reset_daily_clicks(modeladmin, request, queryset):
    for obj in queryset:
        obj.fast_clicks_today = 0
        obj.save(update_fields=['fast_clicks_today'])
reset_daily_clicks.short_description = "Сбросить дневные счетчики кликов"

@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'points_progress',
        'total_points',
        'is_upgraded_badge',
        'fast_clicks_today',
        'last_activity_short',
        'slow_cooldown'
    )
    list_filter = (
        IsUpgradedFilter,
        PointsRangeFilter,
        ('last_activity', admin.DateFieldListFilter),
    )
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    )
    readonly_fields = (
        'total_points',
        'last_activity',
        'slow_cooldown',
        'points_history_link'
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'is_upgraded')
        }),
        ('Баллы', {
            'fields': (
                'points',
                'total_points',
                'fast_clicks_today',
                'points_history_link'
            )
        }),
        ('Активность', {
            'fields': (
                'last_activity',
                'last_slow_click',
                'slow_cooldown'
            )
        }),
    )
    actions = [reset_daily_clicks]
    list_per_page = 30

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'

    def points_progress(self, obj):
        return format_html(
            '<div style="width:100px;background:#ddd;border-radius:3px;">'
            '<div style="width:{}%;background:{};height:20px;border-radius:3px;'
            'color:white;text-align:center;line-height:20px;">{}</div></div>',
            min(100, obj.points / 10),
            '#4CAF50' if obj.points >= 100 else '#2196F3',
            obj.points
        )
    points_progress.short_description = 'Баллы'

    def is_upgraded_badge(self, obj):
        if obj.is_upgraded:
            return format_html(
                '<span style="background:#4CAF50;color:white;padding:2px 6px;'
                'border-radius:10px;">PREMIUM</span>'
            )
        return '-'
    is_upgraded_badge.short_description = 'Статус'
    is_upgraded_badge.admin_order_field = 'is_upgraded'

    def last_activity_short(self, obj):
        if obj.last_activity:
            return obj.last_activity.strftime('%d.%m %H:%M')
        return '-'
    last_activity_short.short_description = 'Был онлайн'
    last_activity_short.admin_order_field = 'last_activity'

    def slow_cooldown(self, obj):
        if obj.last_slow_click:
            remaining = obj.slow_click_cooldown
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() / 60)
                return f"{mins} мин"
        return 'Готово'
    slow_cooldown.short_description = 'Мед. клик'

    def points_history_link(self, obj):
        url = reverse('admin:appname_pointhistory_changelist') + f'?user_points__id__exact={obj.id}'
        return format_html('<a href="{}">История операций ({} записей)</a>', url, obj.history.count())
    points_history_link.short_description = 'История баллов'

@admin.register(PointHistory)
class PointHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'colored_amount',
        'type_badge',
        'created_at_short',
        'reason_short',
        'user_points_link'
    )
    list_filter = (
        'type',
        ('created_at', admin.DateFieldListFilter),
    )
    search_fields = (
        'user_points__user__username',
        'reason',
        'user_points__user__email'
    )
    readonly_fields = (
        'user_points',
        'amount',
        'type',
        'created_at',
        'reason'
    )
    date_hierarchy = 'created_at'
    list_select_related = ('user_points__user',)
    list_per_page = 50

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user_points.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user_points.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user_points__user__username'

    def colored_amount(self, obj):
        color = 'green' if obj.amount > 0 else 'red'
        return format_html(
            '<span style="color:{};font-weight:bold;">{}{}</span>',
            color,
            '+' if obj.amount > 0 else '',
            obj.amount
        )
    colored_amount.short_description = 'Сумма'
    colored_amount.admin_order_field = 'amount'

    def type_badge(self, obj):
        colors = {
            'slow_click': 'blue',
            'fast_click': 'green',
            'spend': 'orange',
            'chat': 'purple',
            'upgrade': 'teal',
            'bonus': 'pink',
            'other': 'gray'
        }
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;'
            'border-radius:10px;font-size:12px;">{}</span>',
            colors.get(obj.type, 'gray'),
            obj.get_type_display()
        )
    type_badge.short_description = 'Тип'
    type_badge.admin_order_field = 'type'

    def created_at_short(self, obj):
        return obj.created_at.strftime('%d.%m %H:%M')
    created_at_short.short_description = 'Дата'
    created_at_short.admin_order_field = 'created_at'

    def reason_short(self, obj):
        return obj.reason[:50] + '...' if obj.reason and len(obj.reason) > 50 else obj.reason or '-'
    reason_short.short_description = 'Причина'

    def user_points_link(self, obj):
        url = reverse('admin:appname_userpoints_change', args=[obj.user_points.id])
        return format_html('<a href="{}">Профиль баллов</a>', url)
    user_points_link.short_description = 'Профиль'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'short_content',
        'timestamp_short',
        'colored_points_spent',
        'is_deleted_badge',
        'content_length'
    )
    list_filter = (
        'is_deleted',
        ('timestamp', admin.DateFieldListFilter),
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'content',
        'user__username',
        'user__email'
    )
    readonly_fields = (
        'user',
        'content',
        'timestamp',
        'points_spent',
        'is_deleted',
        'message_details'
    )
    date_hierarchy = 'timestamp'
    actions = ['soft_delete_messages', 'restore_messages']
    list_per_page = 50
    list_select_related = ('user',)

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'

    def short_content(self, obj):
        content = obj.content
        if obj.is_deleted:
            content = f"<del>{content}</del>"
        return format_html(content[:50] + '...' if len(obj.content) > 50 else content)
    short_content.short_description = 'Сообщение'
    short_content.admin_order_field = 'content'

    def timestamp_short(self, obj):
        return obj.timestamp.strftime('%d.%m %H:%M')
    timestamp_short.short_description = 'Время'
    timestamp_short.admin_order_field = 'timestamp'

    def colored_points_spent(self, obj):
        if obj.points_spent > 0:
            return format_html(
                '<span style="color:red;font-weight:bold;">-{}</span>',
                obj.points_spent
            )
        return '-'
    colored_points_spent.short_description = 'Потрачено'
    colored_points_spent.admin_order_field = 'points_spent'

    def is_deleted_badge(self, obj):
        if obj.is_deleted:
            return format_html(
                '<span style="background:#f44336;color:white;padding:2px 6px;'
                'border-radius:10px;">УДАЛЕНО</span>'
            )
        return format_html(
            '<span style="background:#4CAF50;color:white;padding:2px 6px;'
            'border-radius:10px;">АКТИВНО</span>'
        )
    is_deleted_badge.short_description = 'Статус'
    is_deleted_badge.admin_order_field = 'is_deleted'

    def content_length(self, obj):
        return len(obj.content)
    content_length.short_description = 'Длина'
    content_length.admin_order_field = 'content'

    def message_details(self, obj):
        details = [
            f"Пользователь: {obj.user.username}",
            f"Дата: {obj.timestamp.strftime('%d.%m.%Y %H:%M:%S')}",
            f"Длина: {len(obj.content)} символов",
            f"Потрачено баллов: {obj.points_spent}",
            f"Статус: {'Удалено' if obj.is_deleted else 'Активно'}"
        ]
        return format_html("<br>".join(details))
    message_details.short_description = 'Детали сообщения'

    @admin.action(description='Пометить как удаленные')
    def soft_delete_messages(self, request, queryset):
        updated = 0
        for msg in queryset.filter(is_deleted=False):
            msg.soft_delete()
            updated += 1
        self.message_user(request, f"{updated} сообщений помечено как удаленные")

    @admin.action(description='Восстановить сообщения')
    def restore_messages(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f"{updated} сообщений восстановлено")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')