from django.contrib import admin
from django_salary import models


class UserProfileAdmin(admin.ModelAdmin):
    """
    Настройки отображения, фильтрации и поиска модели:'Category' на панели администратора
    """

    list_display = (
        "user",
        "name",
    )
    list_display_links = (
        "user",
        "name",
    )
    list_editable = (
    )
    list_filter = (
        "user",
        "name",
    )
    # filter_horizontal = (
    #     'users',
    # )
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "user",
                    "name",
                )
            },
        ),
    )
    search_fields = [
        "user",
        "name",
    ]


admin.site.register(models.UserProfile, UserProfileAdmin)


class BaseOrdersAdmin(admin.ModelAdmin):
    """
    Настройки отображения, фильтрации и поиска модели:'Category' на панели администратора
    """

    list_display = (
        "baseorder_numeration",
        "author",
        "parsing_date",
        "parsing_numeration",
        "band_or_performer",
        # "card_name",
        # "korean_price",
        # "price_v_tenge_po_kursu",
        # "price_v_tenge_bez_uchetov",
        # "pribyl",
        # "uchety_obschee_za_razbor",
        # "itogo_po_razboru",
        # "zarplata",
        "track_code",
        "parsing_status",
        "seller_nick",
        # "zarplata_status",
        # "nick_zanyavshego",
        # "oplata_status",
    )
    list_display_links = (
        "baseorder_numeration",
        "author",
        "parsing_date",
        "parsing_numeration",
        "band_or_performer",
        # "card_name",
        # "korean_price",
        # "price_v_tenge_po_kursu",
        # "price_v_tenge_bez_uchetov",
        # "pribyl",
        # "uchety_obschee_za_razbor",
        # "itogo_po_razboru",
        # "zarplata",
        "track_code",
        "parsing_status",
        "seller_nick",
        # "zarplata_status",
        # "nick_zanyavshego",
        # "oplata_status",
    )
    list_editable = (
    )
    list_filter = (
        "baseorder_numeration",
        "author",
        "parsing_date",
        "parsing_numeration",
        "band_or_performer",
        # "card_name",
        # "korean_price",
        # "price_v_tenge_po_kursu",
        # "price_v_tenge_bez_uchetov",
        # "pribyl",
        # "uchety_obschee_za_razbor",
        # "itogo_po_razboru",
        # "zarplata",
        "track_code",
        "parsing_status",
        "seller_nick",
        # "zarplata_status",
        # "nick_zanyavshego",
        # "oplata_status",
    )
    # filter_horizontal = (
    #     'users',
    # )
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "baseorder_numeration",
                    "author",
                    "parsing_date",
                    "parsing_numeration",
                    "band_or_performer",
                    # "card_name",
                    # "korean_price",
                    # "price_v_tenge_po_kursu",
                    # "price_v_tenge_bez_uchetov",
                    # "pribyl",
                    # "uchety_obschee_za_razbor",
                    # "itogo_po_razboru",
                    # "zarplata",
                    "track_code",
                    "parsing_status",
                    "seller_nick",
                    # "zarplata_status",
                    # "nick_zanyavshego",
                    # "oplata_status",
                )
            },
        ),
    )
    search_fields = [
        "baseorder_numeration",
        "author",
        "parsing_date",
        "parsing_numeration",
        "band_or_performer",
        # "card_name",
        # "korean_price",
        # "price_v_tenge_po_kursu",
        # "price_v_tenge_bez_uchetov",
        # "pribyl",
        # "uchety_obschee_za_razbor",
        # "itogo_po_razboru",
        # "zarplata",
        "track_code",
        "parsing_status",
        "seller_nick",
        # "zarplata_status",
        # "nick_zanyavshego",
        # "oplata_status",
    ]


admin.site.register(models.BaseOrders, BaseOrdersAdmin)


class OrdersAdmin(admin.ModelAdmin):
    """
    Настройки отображения, фильтрации и поиска модели:'Category' на панели администратора
    """

    list_display = (
        "order_numeration",
        "base_order",
        # "author",
        # "parsing_date",
        # "parsing_numeration",
        # "band_or_performer",
        "card_name",
        "korean_price",
        "price_v_tenge_po_kursu",
        "price_v_tenge_bez_uchetov",
        "pribyl",
        "uchety_obschee_za_razbor",
        "itogo_po_razboru",
        "zarplata",
        # "track_code",
        # "parsing_status",
        # "seller_nick",
        "zarplata_status",
        "nick_zanyavshego",
        "oplata_status",
    )
    list_display_links = (
        "order_numeration",
        "base_order",
        # "author",
        # "parsing_date",
        # "parsing_numeration",
        # "band_or_performer",
        "card_name",
        "korean_price",
        "price_v_tenge_po_kursu",
        "price_v_tenge_bez_uchetov",
        "pribyl",
        "uchety_obschee_za_razbor",
        "itogo_po_razboru",
        "zarplata",
        # "track_code",
        # "parsing_status",
        # "seller_nick",
        "zarplata_status",
        "nick_zanyavshego",
        "oplata_status",
    )
    list_editable = (
    )
    list_filter = (
        "order_numeration",
        "base_order",
        # "author",
        # "parsing_date",
        # "parsing_numeration",
        # "band_or_performer",
        "card_name",
        "korean_price",
        "price_v_tenge_po_kursu",
        "price_v_tenge_bez_uchetov",
        "pribyl",
        "uchety_obschee_za_razbor",
        "itogo_po_razboru",
        "zarplata",
        # "track_code",
        # "parsing_status",
        # "seller_nick",
        "zarplata_status",
        "nick_zanyavshego",
        "oplata_status",
    )
    # filter_horizontal = (
    #     'users',
    # )
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "order_numeration",
                    "base_order",
                    # "author",
                    # "parsing_date",
                    # "parsing_numeration",
                    # "band_or_performer",
                    "card_name",
                    "korean_price",
                    "price_v_tenge_po_kursu",
                    "price_v_tenge_bez_uchetov",
                    "pribyl",
                    "uchety_obschee_za_razbor",
                    "itogo_po_razboru",
                    "zarplata",
                    # "track_code",
                    # "parsing_status",
                    # "seller_nick",
                    "zarplata_status",
                    "nick_zanyavshego",
                    "oplata_status",
                )
            },
        ),
    )
    search_fields = [
        "order_numeration",
        "base_order",
        # "author",
        # "parsing_date",
        # "parsing_numeration",
        # "band_or_performer",
        "card_name",
        "korean_price",
        "price_v_tenge_po_kursu",
        "price_v_tenge_bez_uchetov",
        "pribyl",
        "uchety_obschee_za_razbor",
        "itogo_po_razboru",
        "zarplata",
        # "track_code",
        # "parsing_status",
        # "seller_nick",
        "zarplata_status",
        "nick_zanyavshego",
        "oplata_status",
    ]


admin.site.register(models.Orders, OrdersAdmin)

# Register your models here.

# class CategoryAdmin(admin.ModelAdmin):
#     """
#     Настройки отображения, фильтрации и поиска модели:'Category' на панели администратора
#     """
#
#     list_display = (
#         "name",
#         "slug",
#     )
#     list_display_links = (
#         "slug",
#     )
#     list_editable = (
#         "name",
#     )
#     list_filter = (
#         "name",
#         "slug",
#     )
#     # filter_horizontal = (
#     #     'users',
#     # )
#     fieldsets = (
#         (
#             "Основное",
#             {
#                 "fields": (
#                     "name",
#                 )
#             },
#         ),
#         (
#             "Техническое",
#             {
#                 "fields": (
#                     "slug",
#                 )
#             },
#         ),
#     )
#     search_fields = [
#         "name",
#         "slug",
#     ]
#
#
# admin.site.register(models.Category, CategoryAdmin)
#
#
# class TovarAdmin(admin.ModelAdmin):
#     """
#     Настройки отображения, фильтрации и поиска модели:'Tovar' на панели администратора
#     """
#
#     list_display = (
#         "title",
#         "slug",
#         "category",
#         "seller",
#         "description",
#         "price",
#         "image",
#         "created",
#     )
#     list_display_links = (
#         "title",
#         "slug",
#     )
#     list_editable = (
#         "price",
#     )
#     list_filter = (
#         "title",
#         "slug",
#         "category",
#         "seller",
#         "description",
#         "price",
#         "image",
#         "created",
#     )
#     # filter_horizontal = (
#     #     'users',
#     # )
#     fieldsets = (
#         (
#             "Основное",
#             {
#                 "fields": (
#                     "title",
#                     "slug",
#                     "category",
#                     "seller",
#                     "description",
#                     "price",
#                     "image",
#                 )
#             },
#         ),
#         (
#             "Техническое",
#             {
#                 "fields": (
#                     "created",
#                 )
#             },
#         ),
#     )
#     search_fields = [
#         "title",
#         "slug",
#     ]
#
#
# admin.site.register(models.Tovar, TovarAdmin)