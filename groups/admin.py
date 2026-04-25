# groups/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Group, Student, ExamSession, ExamResult, ExamControl, AdminPassword, Rules


class StudentInline(admin.StackedInline):
    """Student profilini User admin panelida ko'rsatish"""
    model = Student
    can_delete = False
    verbose_name_plural = 'Student profili'
    fk_name = 'user'
    fields = ['group']
    autocomplete_fields = ['group']


class CustomUserAdmin(UserAdmin):
    """Foydalanuvchi admin panelini sozlash"""
    inlines = [StudentInline]
    list_display = ['username', 'get_full_name', 'email', 'is_staff', 'is_superuser', 'get_group', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'student_profile__group']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'student_profile__group__name']
    readonly_fields = ['last_login', 'date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {'fields': ()}),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'To\'liq ism'
    get_full_name.admin_order_field = 'first_name'
    
    def get_group(self, obj):
        if hasattr(obj, 'student_profile') and obj.student_profile and obj.student_profile.group:
            return obj.student_profile.group.name
        return '-'
    get_group.short_description = 'Guruh'
    get_group.admin_order_field = 'student_profile__group__name'


# User modelini qayta ro'yxatdan o'tkazish
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Guruh admin paneli"""
    list_display = ['name', 'teacher', 'student_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'teacher']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'teacher')
        }),
        ('Vaqt', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'O\'quvchilar soni'
    student_count.admin_order_field = 'students__count'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Student admin paneli"""
    list_display = ['full_name', 'username', 'email', 'group', 'created_at']
    list_filter = ['group', 'user__is_staff']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'group__name']
    raw_id_fields = ['user']
    autocomplete_fields = ['group']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user',)
        }),
        ('Guruh', {
            'fields': ('group',)
        }),
        ('Vaqt', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'To\'liq ism'
    full_name.admin_order_field = 'user__first_name'
    
    def username(self, obj):
        return obj.user.username
    username.short_description = 'Username'
    username.admin_order_field = 'user__username'
    
    def email(self, obj):
        return obj.user.email or '-'
    email.short_description = 'Email'
    email.admin_order_field = 'user__email'
    
    def created_at(self, obj):
        return obj.user.date_joined
    created_at.short_description = 'Ro\'yxatdan o\'tgan sana'
    created_at.admin_order_field = 'user__date_joined'


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    """Imtihon sessiyasi admin paneli"""
    list_display = ['id', 'group', 'is_active', 'started_at', 'ended_at', 'created_by', 'duration']
    list_filter = ['is_active', 'started_at', 'group']
    search_fields = ['group__name', 'created_by__username']
    readonly_fields = ['started_at', 'ended_at']
    raw_id_fields = ['created_by']
    autocomplete_fields = ['group']
    
    fieldsets = (
        ('Imtihon ma\'lumotlari', {
            'fields': ('group', 'is_active', 'created_by')
        }),
        ('Vaqt', {
            'fields': ('started_at', 'ended_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration(self, obj):
        """Imtihon davomiyligini hisoblash"""
        if obj.started_at:
            end = obj.ended_at or obj.started_at
            delta = end - obj.started_at
            minutes = delta.total_seconds() // 60
            return f'{int(minutes)} daqiqa'
        return '-'
    duration.short_description = 'Davomiyligi'


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    """Imtihon natijasi admin paneli"""
    list_display = ['student', 'exam_session', 'score', 'submitted_at', 'answer_count']
    list_filter = ['exam_session__group', 'submitted_at', 'score']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'exam_session__group__name']
    readonly_fields = ['submitted_at', 'answers']
    
    fieldsets = (
        ('Natija ma\'lumotlari', {
            'fields': ('student', 'exam_session', 'score')
        }),
        ('Javoblar', {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
        ('Vaqt', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )
    
    def answer_count(self, obj):
        return len(obj.answers) if obj.answers else 0
    answer_count.short_description = 'Javoblar soni'


@admin.register(ExamControl)
class ExamControlAdmin(admin.ModelAdmin):
    """Imtihon boshqaruvi admin paneli"""
    list_display = ['group', 'is_active', 'started_at', 'status_badge']
    list_filter = ['is_active', 'started_at']
    search_fields = ['group__name']
    readonly_fields = ['started_at']
    autocomplete_fields = ['group']
    
    fieldsets = (
        ('Imtihon boshqaruvi', {
            'fields': ('group', 'is_active')
        }),
        ('Vaqt', {
            'fields': ('started_at',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_active:
            return '🟢 Faol'
        return '🔴 Faol emas'
    status_badge.short_description = 'Holat'


@admin.register(AdminPassword)
class AdminPasswordAdmin(admin.ModelAdmin):
    """Admin parollari admin paneli (faqat superuser ko'radi)"""
    list_display = ['user', 'plain_password_preview', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'updated_at']
    
    fieldsets = (
        ('Admin ma\'lumotlari', {
            'fields': ('user', 'plain_password')
        }),
        ('Vaqt', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def plain_password_preview(self, obj):
        if obj.plain_password:
            return obj.plain_password[:10] + '...' if len(obj.plain_password) > 10 else obj.plain_password
        return '-'
    plain_password_preview.short_description = 'Parol'
    
    def get_queryset(self, request):
        """Faqat superuserlar ko'rishi mumkin"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Rules)
class RulesAdmin(admin.ModelAdmin):
    """Qonun va qoidalar admin paneli"""
    list_display = ['id', 'video_preview', 'images_status', 'rules_preview', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Video', {
            'fields': ('video_url', 'video_file'),
            'classes': ('wide',)
        }),
        ('Rasmlar', {
            'fields': (
                ('image1', 'image1_title', 'image1_description'),
                ('image2', 'image2_title', 'image2_description'),
            ),
        }),
        ('Qoidalar matni', {
            'fields': ('rules_text',),
        }),
        ('Vaqt', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def video_preview(self, obj):
        if obj.video_url:
            return f'<a href="{obj.video_url}" target="_blank">📹 YouTube</a>'
        elif obj.video_file:
            return '📁 Video fayl'
        return '❌ Video yo\'q'
    video_preview.short_description = 'Video'
    video_preview.allow_tags = True
    
    def images_status(self, obj):
        images = []
        if obj.image1:
            images.append('✅ Rasm 1')
        else:
            images.append('❌ Rasm 1')
        if obj.image2:
            images.append('✅ Rasm 2')
        else:
            images.append('❌ Rasm 2')
        return ' | '.join(images)
    images_status.short_description = 'Rasmlar holati'
    
    def rules_preview(self, obj):
        if obj.rules_text:
            preview = obj.rules_text[:50]
            return preview + '...' if len(obj.rules_text) > 50 else preview
        return '-'
    rules_preview.short_description = 'Qoidalar (qisqacha)'
    
    def has_add_permission(self, request):
        """Faqat bitta qator bo'lishi mumkin"""
        if Rules.objects.exists():
            return False
        return True


# ============ ADMIN PANEL UCHUN QO'SHIMCHA SOZLAMALAR ============

# Admin panel sarlavhasini o'zgartirish
admin.site.site_header = 'Guruhlar Boshqaruvi - Admin Panel'
admin.site.site_title = 'Guruhlar Admin'    
admin.site.index_title = 'Boshqaruv paneliga xush kelibsiz'


# ============ QO'SHIMCHA ACTIONLAR ============

@admin.action(description='Tanlangan guruhlarni faollashtirish')
def activate_groups(modeladmin, request, queryset):
    """Guruhlarni faollashtirish (agar qo'shimcha maydon bo'lsa)"""
    updated = queryset.update(is_active=True) if hasattr(Group, 'is_active') else 0
    modeladmin.message_user(request, f'{updated} ta guruh faollashtirildi.')


@admin.action(description='Tanlangan imtihonlarni to\'xtatish')
def stop_exam_sessions(modeladmin, request, queryset):
    """Tanlangan imtihonlarni to'xtatish"""
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f'{updated} ta imtihon to\'xtatildi.')


# Agar Group modelida is_active maydoni bo'lsa (ixtiyoriy)
# GroupAdmin.actions = [activate_groups]

# ExamSession adminiga action qo'shish
ExamSessionAdmin.actions = [stop_exam_sessions]