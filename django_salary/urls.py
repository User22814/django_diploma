from django.urls import re_path, path
from django_salary import views

urlpatterns = [
    re_path(r"^register/$", views.profile_register, name="profile_register"),
    re_path(r"^login/$", views.profile_login, name="profile_login"),
    re_path(r"^logout/$", views.profile_logout, name="profile_logout"),

    path("baseorder/", views.baseorder_list, name="baseorder_list"),

    # path("test_csv/", views.test_csv, name="test_csv"),

    # path("olx/category/<slug:slug>/", views.category, name="category"),
    path("baseorder/detail/<int:pk>/", views.order_list, name="baseorder_detail"),

    path("baseorder/register/", views.baseorder_register, name="baseorder_register"),

    path("baseorder/update/<int:pk>/", views.baseorder_update, name="baseorder_update"),

    path("baseorder/delete/<int:pk>/", views.baseorder_delete, name="baseorder_delete"),

    # re_path(r"^olx/tovar/detail/$", views.tovar_detail, name="tovar_detail"),

    # re_path(r"^olx/tovar/create/$", views.tovar_create, name="tovar_create"),

    path("orders/register/<int:baseorder_pk>/", views.order_register, name="order_register"),

    path("orders/update/<int:pk_id>/", views.order_update, name="order_update"),

    path("orders/delete/<int:pk_id>/", views.order_delete, name="order_delete"),

    path("orders/statistic/", views.user_statistic, name="user_statistic"),

    path("orders/zp_bool_change/<int:pk_id>/", views.zp_bool_change, name="zp_bool_change"),

    path("orders/for_staff/", views.order_list_for_staff, name="order_list_for_staff"),

    path("orders/for_staff/update/<int:pk_id>/", views.order_update_for_staff, name="order_update_for_staff"),

    path("get_plot/", views.get_plot, name="get_plot"),

    path("salary/", views.raspredelenie_zp, name="salary"),

    path("change_salary/<int:pk_id>/", views.change_raspredelenie_zp, name="change_salary"),

    path("orders/download_excel_statistic/", views.download_excel_statistic, name="download_excel_statistic"),

    path("main/", views.order_list_for_unregistered, name="order_list_for_unregistered"),

]
