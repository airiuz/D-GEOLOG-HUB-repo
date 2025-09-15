from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = CustomUser
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('pk',)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_blocked",
    )

    add_fieldsets = (
        (
            _("Personal info"),
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                )
            }
        ),
        (
            _("Set password"),
            {
                "fields": (
                    "password1",
                    "password2"
                ),
            },
        ),
    )
    fieldsets = (
        (
            _("Personal info"),
            {"fields": (
                "email",
                "first_name",
                "last_name"
            )
            }
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_blocked"
                ),
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined"
                )
            }
        )
    )





admin.site.register(CustomUser, CustomUserAdmin)
admin.site.site_header = 'My project'  # default: "Django Administration"
admin.site.index_title = 'Features area'  # default: "Site administration"
admin.site.unregister(Group)
