from django import forms
from django.contrib import admin, messages
from django.core import management
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from apps.products.models import Category, DictImageColor, ImageColorItem, Item, Size, Specialization, XlsxUpload
from apps.products.tasks import clear_deps


@admin.action(description='Опубликован')
def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)


@admin.action(description='Не опубликован')
def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)


@admin.action(description='Хит')
def make_hit(modeladmin, request, queryset):
    queryset.update(is_hit=True)


@admin.action(description='Не хит')
def make_not_hit(modeladmin, request, queryset):
    queryset.update(is_hit=False)


@admin.action(description='Умное удаление')
def remove_items(modeladmin, request, queryset):
    for item in queryset.all():
        clear_deps(item)
        item.delete()


@admin.register(XlsxUpload)
class XlsxUploadAdmin(admin.ModelAdmin):
    model = XlsxUpload

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super(XlsxUploadAdmin, self).save_model(request, obj, form, change)
        log = management.call_command('load_products', obj.file.path)
        if log:
            messages.add_message(request, messages.WARNING, "Errors while import, see log!")
            obj.result = log
            obj.save()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category

    # list_display = ("name",)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    model = Specialization


class ItemSizeAdmin(admin.TabularInline):
    model = Size.item.through
    extra = 1


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    pass


@admin.register(DictImageColor)
class DictImageColorAdmin(admin.ModelAdmin):
    model = DictImageColor
    list_display = ("color",)

    def color(self, obj):
        result = f"{obj.id}: {obj.name}"
        if obj.name_eng:
            result += f" ({obj.name_eng})"
        result += f" - {obj.color_code}"
        back_color = ('#000000' if obj.color_code != '#000000' else '#FFFFFF')
        print(obj.id, result, back_color)
        return mark_safe(f"<span style='color:{obj.color_code}; background-color:{back_color}'>{result}</span>")


class ImageColorItemAdmin(admin.TabularInline):
    model = ImageColorItem


class MyItemAdminForm(forms.ModelForm):
    def check_main_color_present(self, total_forms):
        main_color_count = 0
        for color_row in range(total_forms):
            if self.data.get(f"onitem-{color_row}-is_main_color") == "on":
                main_color_count += 1

        if main_color_count == 0:
            raise ValidationError(_("Обязательно должен быть установлен основной цвет!"))
        elif main_color_count > 1:
            raise ValidationError(_("Основной цвет должен быть только один!"))

    def check_main_image_present(self, total_forms):
        colors = set([self.data.get(f"onitem-{color_row}-color") for color_row in range(total_forms)
                      if self.data.get(f"onitem-{color_row}-color") != ""])
        for color in colors:
            main_image_count = 0
            for color_row in range(total_forms):
                if self.data.get(f"onitem-{color_row}-color") == color \
                        and self.data.get(f"onitem-{color_row}-is_main_image") == "on":
                    main_image_count += 1

            if main_image_count == 0:
                color_name = DictImageColor.objects.get(id=color).name
                raise ValidationError(
                    _(f"Для цвета {color_name} с id={color} обязательно должно быть установлено основное изображение!"))
            elif main_image_count > 1:
                color_name = DictImageColor.objects.get(id=color).name
                raise ValidationError(
                    _(f"Для цвета {color_name} с id={color} должно быть только одно основное изображение!"))

    def clean(self):
        super().clean()
        total_forms = int(self.data.get("onitem-TOTAL_FORMS"))

        self.check_main_color_present(total_forms)
        self.check_main_image_present(total_forms)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    model = Item
    form = MyItemAdminForm
    inlines = (ImageColorItemAdmin, )
    actions = [make_published, make_unpublished, make_hit, make_not_hit, remove_items]
    list_display = ("name", "main_image", "specialization", "category", "price", "short_description")
    fieldsets = (
        (None, {'fields': ('name', 'price')}),
        ('Category, Specializations:', {'fields': ('category', 'specialization')}),
        ('Desscription:', {'fields': ('description', 'short_description')}),
        ('Flags:', {'fields': ('is_published', 'is_hit'), 'classes': ('collapse',)}),
        ('Sizes:', {'fields': ('size',)}),
    )

    def main_image(self, obj):
        main_color = ImageColorItem.objects.filter(
            item_id=obj.id, is_main_color=True).values_list("color_id", flat=True).first()
        main_image = ImageColorItem.objects.get(item_id=obj.id, color_id=main_color, is_main_image=True).image
        if bool(main_image.url):
            return mark_safe(f"<img src='{main_image.url}' width=50>")
        else:
            return mark_safe("нет изображения")
