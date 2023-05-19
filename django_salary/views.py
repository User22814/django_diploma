import sys
import psutil
import requests

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest, FileResponse
from django.shortcuts import render, redirect
import re
import csv
import time
from django_salary import models
from decimal import Decimal
from datetime import datetime, timedelta
from openpyxl import Workbook
from django.http import HttpResponse
import xlwt
import plotly.graph_objs as go
import plotly.offline as opy
from django.core.cache import caches
from django_salary.utils import logging
from django.views.decorators.cache import cache_page


default_cache = caches['default']
MULTIPLY = 6
MAX_RAM_SIZE = 800

KURS_OBMENA = 2.6083


def cache(key: str, function_queryset: any) -> any:
    memory_usage = psutil.Process().memory_info().rss
    memory_usage = memory_usage / 1024 / 1024
    # print(f"Доступно: {MAX_RAM_SIZE - memory_usage} мб")
    if memory_usage <= MAX_RAM_SIZE:
        # print("В cache RAM хватает")
        result = default_cache.get(key)
        if result:
            return result
        result = function_queryset()
        if key != "parsing_kurs_obmena_cache":
            default_cache.set(key, result, timeout=10 * MULTIPLY)
        else:
            default_cache.set(key, result, timeout=7200)
    else:
        # print("В cache RAM не хватает")
        result = function_queryset()
    return result


def update_cache(key: str, function_queryset: any) -> any:
    memory_usage = psutil.Process().memory_info().rss
    memory_usage = memory_usage / 1024 / 1024
    # print(f"Доступно в update_cache: {MAX_RAM_SIZE - memory_usage} мб")
    if memory_usage <= MAX_RAM_SIZE:
        # print("В update_cache RAM хватает")
        result = function_queryset()
        default_cache.set(key, result, timeout=10 * MULTIPLY)
        # print(result)
    else:
        # print("В update_cache RAM не хватает")
        default_cache.delete(key)
    return True


def time_measure(func):
    def wrapper(*args, **kwargs):
        time_start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"time elapsed: {round(time.perf_counter() - time_start, 5)}")
        return result

    return wrapper


# КЭШ
# С помощью библиотеки для визуализации данных выводить график статистики
# Вывод в excel фильтрованных данных

ZP_dict = {"admin": 0.3, "yoonarie": 1}


def test_csv(request: HttpRequest):
    if request.method == "GET":
        current_date = datetime.now()
        file_name = current_date.strftime("%Y-%m-%d")
        one_day_ago = current_date - timedelta(days=1)
        base_orders_objs = models.BaseOrders.objects.filter(created__gte=one_day_ago, created__lte=current_date)

        with open(f"static/media/csv_db/orders_{file_name}.csv", mode="w") as w_file:

            file_writer = csv.writer(w_file, delimiter="#", lineterminator="\r")

            for obj in base_orders_objs:
                file_writer.writerow([obj.author.username, obj.parsing_date.strftime('%Y-%m-%d'),
                                      obj.parsing_numeration, obj.band_or_performer, obj.track_code,
                                      obj.seller_nick, obj.created.strftime('%Y-%m-%d')])

        orders_objs = models.Orders.objects.filter(created__gte=one_day_ago, created__lte=current_date)

        with open(f"static/media/csv_db/baseorders_{file_name}.csv", mode="w") as w_file:

            file_writer = csv.writer(w_file, delimiter="#", lineterminator="\r")

            for obj in orders_objs:
                file_writer.writerow([obj.base_order.parsing_numeration, obj.card_name, float(obj.korean_price),
                                      obj.kurs_obmena, float(obj.price_v_tenge_po_kursu),
                                      float(obj.price_v_tenge_bez_uchetov), float(obj.pribyl),
                                      float(obj.uchety_obschee_za_razbor), float(obj.itogo_po_razboru),
                                      float(obj.zarplata), obj.parsing_status, obj.zarplata_status,
                                      obj.nick_zanyavshego, obj.oplata_status, obj.created.strftime('%Y-%m-%d')])

        return render(request, "django_salary/components/error.html",
                      context={"error": f"GOOD"})


@logging
def profile_register(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        user = request.user
        if user.is_authenticated:
            return redirect('baseorder_list')
        else:
            return render(request, "django_salary/profile_register.html", context={"error": ""})
    elif request.method == "POST":
        name = request.POST["name"]
        username = request.POST["username"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            # raise Exception("incorrect password")
            return render(request, "django_salary/profile_register.html",
                          context={"error": f"password1 и password2 не одинаковы"})

        # pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])[A-Za-z\d!@#$%^&*()_+]{8,}$'

        # if not re.match(pattern, password1):
        if len(password1) < 5:
            # raise Exception("Пароль должен содержать минимум 8 символов, одну заглавную, одну строчную букву и одно число")
            return render(request, "django_salary/profile_register.html", context={"error": "Пароль должен содержать минимум 4 символов"})

        if len(User.objects.filter(username=username)) > 0:
            return render(request, "django_salary/profile_register.html",
                          context={"error": f"Пользователь с username: {username} уже существует"})

        user = User.objects.create_user(
            username=username,
            password=password1
        )

        models.UserProfile.objects.create(
            user=user,
            name=name
        )
        return redirect("profile_login")


@logging
# @cache_page(60 * 5)
def profile_login(request: HttpRequest):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            return redirect('baseorder_list')
        else:
            return render(request, 'django_salary/profile_login.html', context={})
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # print(username)
        # print(password)
        user = authenticate(request, username=username, password=password)
        # print(user)
        if user is None:
            # raise Exception("incorrect password")
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Введенный пароль неверный"})
        login(request, user)
        return redirect('baseorder_list')


@logging
def profile_logout(request: HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return redirect('profile_login')
    logout(request)
    return redirect('order_list_for_unregistered')


def parsing_kurs_obmena_cache():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.0.0 Safari/537.36'
    }
    response = requests.get(url="https://paysend.com/ru-us/otpravit-dengi/iz-kazahstana-v-yuzhnuyu-koreyu", headers=headers)
    kurs = response.text.split(sep='1.00 KZT = ')[1].split("KRW")[0].strip()
    return float(kurs)


# TODO BaseOrders
def baseorder_list_cache(user_obj):
    if user_obj.is_superuser:
        baseorders = models.BaseOrders.objects.all()
    else:
        baseorders = models.BaseOrders.objects.filter(author=user_obj)
    result = []
    # last_baseorder = baseorders.last()
    # last_parsing_numeration = last_baseorder.parsing_numeration
    index = 1
    for baseorder in baseorders:
        dict_tmp = {
            # "baseorder_numeration": baseorder.baseorder_numeration,
            "baseorder_numeration": index,
            "author": baseorder.author.username,
            "parsing_numeration": baseorder.parsing_numeration,
            "parsing_date": baseorder.parsing_date.strftime('%d.%m.%Y'),
            "count": baseorder.get_count_of_orders(),
            "band_or_performer": baseorder.band_or_performer,
            "track_code": baseorder.track_code,
            # "parsing_status": baseorder.parsing_status,
            "seller_nick": baseorder.seller_nick,
        }
        index += 1
        result.append(dict_tmp)
    return result


@logging
def baseorder_list(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        # users_ins = cache(key="users_filter_active", function_queryset=lambda: User.objects.filter(is_active=True))
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        result = cache(key=f"baseorder_list_{user.username}", function_queryset=lambda: baseorder_list_cache(user))
        # print(result)
        # print(f"size in baseorder_list: {sys.getsizeof(result)} bytes")
        memory_usage = psutil.Process().memory_info().rss
        # print(f"size in baseorder_list: {round(sys.getsizeof(result) / 1024 / 1024, 5)} megabytes")
        # print(f"Memory usage: {memory_usage / 1024 / 1024} megabytes")
        if len(result) != 0:
            last_elem = result[-1]
            last_parsing_numeration = last_elem["parsing_numeration"]
        else:
            last_parsing_numeration = 0

        return render(request, "django_salary/baseorder_list.html", context={"orders": result,
                                                                             "last_parsing_numeration": last_parsing_numeration})


@logging
def baseorder_update(request: HttpRequest, pk):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if user.is_superuser:
            baseorder_obj = models.BaseOrders.objects.get(parsing_numeration=pk)
        else:
            baseorder_obj = models.BaseOrders.objects.get(author=user, parsing_numeration=pk)
        result = {
            # "baseorder_numeration": baseorder_obj.baseorder_numeration,
            "parsing_date": baseorder_obj.parsing_date.strftime('%Y-%m-%d'),
            "parsing_numeration": baseorder_obj.parsing_numeration,
            "band_or_performer": baseorder_obj.band_or_performer,
            "track_code": baseorder_obj.track_code,
            # "parsing_status": baseorder_obj.parsing_status,
            "seller_nick": baseorder_obj.seller_nick,
        }
        return render(request, "django_salary/baseorder_update.html", context={"baseorder_obj": result})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не авторизованы"})
        parsing_date = request.POST.get("parsing_date", None)
        # parsing_numeration = request.POST.get("parsing_numeration", None)
        band_or_performer = request.POST.get("band_or_performer", None)
        track_code = request.POST.get("track_code", None)
        # parsing_status = request.POST.get("parsing_status", None)
        seller_nick = request.POST.get("seller_nick", None)

        # Проверка формата даты
        if "-" in parsing_date:
            if parsing_date.count("-") != 2:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"parsing_date введено неправильно. Проверьте формат"})

        # Проверка, чтобы данные приходили на бэк
        if parsing_date is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_date is None"})

        # if parsing_numeration is None:
        #     return render(request, "django_salary/components/error.html", context={"error": f"parsing_numeration is None"})

        if band_or_performer is None:
            return render(request, "django_salary/components/error.html", context={"error": f"band_or_performer is None"})

        if track_code is None:
            return render(request, "django_salary/components/error.html", context={"error": f"track_code is None"})

        # if parsing_status is None:
        #     return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

        if seller_nick is None:
            return render(request, "django_salary/components/error.html", context={"error": f"seller_nick is None"})

        # Проверка, чтобы пустые данные не приходили
        if parsing_date == "":
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_date пусто"})

        # if parsing_numeration == "":
        #     return render(request, "django_salary/components/error.html", context={"error": f"parsing_numeration пусто"})

        if band_or_performer == "":
            return render(request, "django_salary/components/error.html", context={"error": f"band_or_performer пусто"})

        if seller_nick == "":
            return render(request, "django_salary/components/error.html", context={"error": f"seller_nick пусто"})

        user = request.user

        if user.is_superuser:
            baseorder_objs = models.BaseOrders.objects.filter(parsing_numeration=pk)
        else:
            baseorder_objs = models.BaseOrders.objects.filter(author=user, parsing_numeration=pk)

        if len(baseorder_objs) == 0:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Системная ошибка: BaseOrder не найден"})

        baseorder_obj = baseorder_objs[0]

        flag_save = False

        parsing_date_old = None

        if parsing_date != baseorder_obj.parsing_date:
            parsing_date_old = baseorder_obj.parsing_date
            baseorder_obj.parsing_date = parsing_date
            flag_save = True

        # if parsing_numeration != baseorder_obj.parsing_numeration:
        #     baseorder_obj.parsing_numeration = parsing_numeration
        #     flag_save = True

        band_or_performer_old = None

        if band_or_performer.lower().strip() != baseorder_obj.band_or_performer:
            band_or_performer_old = baseorder_obj.band_or_performer
            baseorder_obj.band_or_performer = band_or_performer.lower().strip()
            flag_save = True

        track_code_old = None

        if track_code != baseorder_obj.track_code:
            track_code_old = baseorder_obj.track_code
            baseorder_obj.track_code = track_code
            flag_save = True

        # if parsing_status != baseorder_obj.parsing_status:
        #     baseorder_obj.parsing_status = parsing_status
        #     flag_save = True

        seller_nick_old = None

        if seller_nick != baseorder_obj.seller_nick:
            seller_nick_old = baseorder_obj.seller_nick
            baseorder_obj.seller_nick = seller_nick
            flag_save = True

        if flag_save:
            baseorder_obj.save()
            text = f"Владелец: {baseorder_obj.author.username} Номер разбора: {pk} | "
            if parsing_date_old is not None:
                text += f"parsing_date: {parsing_date_old.strftime('%Y-%m-%d')} -> {parsing_date_old} | "
            if band_or_performer_old is not None:
                text += f"band_or_performer: {band_or_performer_old} -> {band_or_performer.lower().strip()} | "
            if track_code_old is not None:
                text += f"track_code: {track_code_old} -> {track_code} | "
            if seller_nick_old is not None:
                text += f"seller_nick: {seller_nick_old} -> {seller_nick} | "
            text = text[:-2]
            models.ActivityLoggingModel.objects.create(
                username=user.username,
                myself=user == baseorder_obj.author,
                activity="baseorder_update",
                text=text,
            )
            update_cache(key=f"baseorder_list_{user.username}", function_queryset=lambda: baseorder_list_cache(user))
            if baseorder_obj.author != user and user.is_superuser:
                # print("baseorder_update: BaseOrder List обновлен")
                update_cache(key=f"baseorder_list_{baseorder_obj.author.username}", function_queryset=lambda: baseorder_list_cache(baseorder_obj.author))

        return redirect("baseorder_list")


@logging
def baseorder_delete(request: HttpRequest, pk):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if user.is_superuser:
            baseorder_objs = models.BaseOrders.objects.filter(parsing_numeration=pk)
        else:
            baseorder_objs = models.BaseOrders.objects.filter(author=user, parsing_numeration=pk)
        if len(baseorder_objs) == 0:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Системная ошибка: BaseOrder не найден"})
        baseorder_obj = baseorder_objs[0]
        author = baseorder_obj.author
        baseorder_obj.delete()
        models.ActivityLoggingModel.objects.create(
            username=user.username,
            myself=user == author,
            activity="baseorder_delete",
            text=f"Владелец: {author} Номер разбора: {pk}",
        )
        update_cache(key=f"baseorder_list_{user.username}", function_queryset=lambda: baseorder_list_cache(user))
        if author != user and user.is_superuser:
            # print("baseorder_delete: BaseOrder List обновлен")
            update_cache(key=f"baseorder_list_{author.username}", function_queryset=lambda: baseorder_list_cache(author))
        return redirect("baseorder_list")


@logging
def baseorder_register(request: HttpRequest):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        baseorder_objs = models.BaseOrders.objects.all()
        if len(baseorder_objs) != 0:
            last_baseorder_obj = baseorder_objs.last()
            last_numeration = last_baseorder_obj.parsing_numeration
        else:
            last_numeration = 0
        return render(request, "django_salary/baseorder_create.html", context={"last_numeration": last_numeration})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не авторизованы"})
        parsing_date = request.POST.get("parsing_date", None)
        parsing_numeration = request.POST.get("parsing_numeration", None)
        band_or_performer = request.POST.get("band_or_performer", None)
        track_code = request.POST.get("track_code", None)
        # parsing_status = request.POST.get("parsing_status", None)
        seller_nick = request.POST.get("seller_nick", None)

        # Проверка формата даты
        if "-" in parsing_date:
            if parsing_date.count("-") != 2:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"parsing_date введено неправильно. Проверьте формат"})

        # Проверка, чтобы данные приходили на бэк
        if parsing_date is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_date is None"})

        if parsing_numeration is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_numeration is None"})

        if band_or_performer is None:
            return render(request, "django_salary/components/error.html", context={"error": f"band_or_performer is None"})

        if track_code is None:
            return render(request, "django_salary/components/error.html", context={"error": f"track_code is None"})

        # if parsing_status is None:
        #     return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

        if seller_nick is None:
            return render(request, "django_salary/components/error.html", context={"error": f"seller_nick is None"})

        # Проверка, чтобы пустые данные не приходили
        if parsing_date == "":
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_date пусто"})

        if parsing_numeration == "":
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_numeration пусто"})

        if band_or_performer == "":
            return render(request, "django_salary/components/error.html", context={"error": f"band_or_performer пусто"})

        if seller_nick == "":
            return render(request, "django_salary/components/error.html", context={"error": f"seller_nick пусто"})

        user = request.user

        baseorder_objs_all = models.BaseOrders.objects.all()

        baseorder_obj_all_last = baseorder_objs_all.last()
        if len(baseorder_objs_all) != 0:
            if int(parsing_numeration) <= baseorder_obj_all_last.parsing_numeration:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Номер разбора не может быть меньше или равно {baseorder_obj_all_last.parsing_numeration}"})

        # baseorder_objs = baseorder_objs_all.filter(author=user)

        # next_numeration = 0

        # if len(baseorder_objs) == 0:
        #     next_numeration = 1
        # else:
        #     # for order_obj in baseorder_objs:
        #     #     list_of_numeration.append(order_obj.baseorder_numeration)
        #     # next_numeration = max(list_of_numeration) + 1
        #     next_numeration = baseorder_objs.last().baseorder_numeration + 1

        models.BaseOrders.objects.create(
            # baseorder_numeration=next_numeration,
            author=user,
            parsing_date=parsing_date,
            parsing_numeration=int(parsing_numeration),
            band_or_performer=band_or_performer.lower().strip(),
            track_code=track_code,
            # parsing_status=parsing_status,
            seller_nick=seller_nick,
        )

        models.ActivityLoggingModel.objects.create(
            username=user.username,
            myself=True,
            activity="baseorder_register",
            text=f"Номер разбора: {parsing_numeration}",
        )

        update_cache(key=f"baseorder_list_{user.username}", function_queryset=lambda: baseorder_list_cache(user))

        # return redirect("profile_login")
        return redirect("baseorder_list")
        # return redirect("order_register")


# TODO Order
def order_list_cache(base_order_obj):
    order_objs = models.Orders.objects.filter(base_order=base_order_obj)  # (1, 'Электроника', 'electro')
    result = []
    index = 1
    for order_obj in order_objs:
        dict_tmp = {
            "id": order_obj.id,
            # "order_numeration": order_obj.order_numeration,
            "order_numeration": index,
            "author": order_obj.base_order.author.username,
            "parsing_date": order_obj.base_order.parsing_date.strftime('%d.%m.%Y'),
            "parsing_numeration": order_obj.base_order.parsing_numeration,
            "band_or_performer": order_obj.base_order.band_or_performer,
            "card_name": order_obj.card_name,
            "korean_price": order_obj.korean_price,
            "price_v_tenge_bez_uchetov": order_obj.price_v_tenge_bez_uchetov,
            "pribyl": order_obj.pribyl,
            "uchety_obschee_za_razbor": order_obj.uchety_obschee_za_razbor,
            "zarplata": order_obj.zarplata,
            "track_code": order_obj.base_order.track_code,
            "parsing_status": order_obj.parsing_status,
            "seller_nick": order_obj.base_order.seller_nick,
            "zarplata_status": "-" if order_obj.parsing_status == "Возврат" else order_obj.zarplata_status,
            "nick_zanyavshego": order_obj.nick_zanyavshego,
            "oplata_status": order_obj.oplata_status,
        }
        index += 1
        result.append(dict_tmp)
    return result


@logging
def order_list(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if user.is_superuser:
            base_orders = models.BaseOrders.objects.filter(parsing_numeration=pk)
        else:
            base_orders = models.BaseOrders.objects.filter(parsing_numeration=pk, author=request.user)
        if len(base_orders) == 0 or len(base_orders) > 1:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"BaseOrder с номером {pk} у Пользователя {request.user.username} нет или больше одного"})
        base_order = base_orders[0]
        result = cache(key=f"baseorder_detail_{pk}_{user.username}", function_queryset=lambda: order_list_cache(base_order))
        return render(request, "django_salary/order_list.html", context={"order_objs": result, "baseorder_pk": pk})


@logging
def order_register(request: HttpRequest, baseorder_pk: int):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        return render(request, "django_salary/order_create.html", context={"baseorder_pk": baseorder_pk})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не авторизованы"})
        # print(request.POST)
        # parsing_date = request.POST.get("parsing_date", None)
        # parsing_numeration = request.POST.get("parsing_numeration", None)
        # band_or_performer = request.POST.get("band_or_performer", None)
        card_name = request.POST.get("card_name", None)
        korean_price = request.POST.get("korean_price", None)
        uchety_obschee_za_razbor = request.POST.get("uchety_obschee_za_razbor", None)
        price_v_tenge_bez_uchetov = request.POST.get("price_v_tenge_bez_uchetov", None)
        parsing_status = request.POST.get("parsing_status", None)
        # track_code = request.POST.get("track_code", None)
        # seller_nick = request.POST.get("seller_nick", None)
        nick_zanyavshego = request.POST.get("nick_zanyavshego", None)
        oplata_status_str = request.POST.get("oplata_status", "")

        if oplata_status_str == "on":
            oplata_status = True
        else:
            oplata_status = False

        if card_name is None:
            return render(request, "django_salary/components/error.html", context={"error": f"card_name is None"})

        if korean_price is None:
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price is None"})

        if price_v_tenge_bez_uchetov is None:
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov is None"})

        if uchety_obschee_za_razbor is None:
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor is None"})

        if parsing_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

        if nick_zanyavshego is None:
            return render(request, "django_salary/components/error.html", context={"error": f"nick_zanyavshego is None"})

        if oplata_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"oplata_status is None"})

        # Проверка, чтобы пустые данные не приходили

        if card_name == "":
            return render(request, "django_salary/components/error.html", context={"error": f"card_name пусто"})

        if korean_price == "":
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price пусто"})

        if price_v_tenge_bez_uchetov == "":
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov пусто"})

        if uchety_obschee_za_razbor == "":
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor пусто"})

        if parsing_status == "":
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status пусто"})

        if nick_zanyavshego == "":
            return render(request, "django_salary/components/error.html", context={"error": f"nick_zanyavshego пусто"})

        if oplata_status == "":
            return render(request, "django_salary/components/error.html", context={"error": f"oplata_status пусто"})

        user = request.user

        if user.is_superuser:
            baseorder_objs = models.BaseOrders.objects.filter(parsing_numeration=baseorder_pk)
        else:
            baseorder_objs = models.BaseOrders.objects.filter(author=user, parsing_numeration=baseorder_pk)

        if len(baseorder_objs) == 0:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Системная ошибка: BaseOrder не найден"})

        baseorder_obj = baseorder_objs[0]

        # order_objs = models.Orders.objects.filter(base_order=baseorder_obj)

        # next_numeration = 0
        #
        # if len(order_objs) != 0:
        #     # for order_obj in order_objs:
        #     #     list_of_numeration.append(order_obj.order_numeration)
        #     next_numeration = order_objs.last().order_numeration + 1
        # elif len(order_objs) == 0:
        #     next_numeration = 1

        korean_price = float(korean_price)
        price_v_tenge_bez_uchetov = float(price_v_tenge_bez_uchetov)
        uchety_obschee_za_razbor = float(uchety_obschee_za_razbor)

        if user.is_superuser:
            kurs_obmena = cache(key=f"parsing_kurs_obmena_cache", function_queryset=lambda: parsing_kurs_obmena_cache())
        else:
            kurs_obmena = KURS_OBMENA

        price_v_tenge_po_kursu = korean_price * 10000 / kurs_obmena

        pribyl = price_v_tenge_bez_uchetov - price_v_tenge_po_kursu

        itogo_po_razboru = price_v_tenge_bez_uchetov + uchety_obschee_za_razbor

        userprofiles = models.UserProfile.objects.filter(user=user)

        if len(userprofiles) == 0 or len(userprofiles) > 1:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"UserProfile не найдено или больше одного"})

        userprofile = userprofiles[0]

        if userprofile.zp is None or userprofile.zp == 0:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Зарплата у Пользователя {user.username} не установлена."})

        zarplata = pribyl * userprofile.zp / 100

        models.Orders.objects.create(
            # order_numeration=next_numeration,
            base_order=baseorder_obj,
            card_name=card_name.lower().strip(),
            korean_price=Decimal(korean_price),
            kurs_obmena=Decimal(kurs_obmena),
            price_v_tenge_po_kursu=Decimal(price_v_tenge_po_kursu),
            price_v_tenge_bez_uchetov=Decimal(price_v_tenge_bez_uchetov),
            pribyl=Decimal(pribyl),
            uchety_obschee_za_razbor=Decimal(uchety_obschee_za_razbor),
            itogo_po_razboru=Decimal(itogo_po_razboru),
            zarplata=Decimal(zarplata),
            parsing_status=parsing_status,
            nick_zanyavshego=nick_zanyavshego,
            oplata_status=oplata_status,
        )

        models.ActivityLoggingModel.objects.create(
            username=user.username,
            myself=user == baseorder_obj.author,
            activity="order_register",
            text=f"Владелец: {baseorder_obj.author} Номер разбора: {baseorder_obj.parsing_numeration}",
        )

        update_cache(key=f"baseorder_detail_{baseorder_obj.parsing_numeration}_{user.username}",
                     function_queryset=lambda: order_list_cache(baseorder_obj))

        if baseorder_obj.author != user and user.is_superuser:
            # print("order_register: BaseOrder detail обновлено")
            update_cache(key=f"baseorder_detail_{baseorder_obj.parsing_numeration}_{baseorder_obj.author.username}",
                         function_queryset=lambda: order_list_cache(baseorder_obj))
            update_cache(key=f"baseorder_list_{baseorder_obj.author.username}", function_queryset=lambda: baseorder_list_cache(baseorder_obj.author))

        return redirect("baseorder_detail", baseorder_pk)


@logging
def order_update(request: HttpRequest, pk_id: int):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        order_obj = models.Orders.objects.get(id=pk_id)
        result = {
            "card_name": order_obj.card_name,
            "korean_price": float(order_obj.korean_price),
            "uchety_obschee_za_razbor": int(float(order_obj.uchety_obschee_za_razbor)),
            "price_v_tenge_bez_uchetov": int(float(order_obj.price_v_tenge_bez_uchetov)),
            "parsing_status": order_obj.parsing_status,
            "nick_zanyavshego": order_obj.nick_zanyavshego,
            "oplata_status": order_obj.oplata_status,
        }
        # print(result['korean_price'])
        # print(type(result['korean_price']))
        return render(request, "django_salary/order_update.html", context={"pk_id": pk_id, "order_obj": result})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не авторизованы"})
        card_name = request.POST.get("card_name", None)
        korean_price = request.POST.get("korean_price", None)
        uchety_obschee_za_razbor = request.POST.get("uchety_obschee_za_razbor", None)
        price_v_tenge_bez_uchetov = request.POST.get("price_v_tenge_bez_uchetov", None)
        nick_zanyavshego = request.POST.get("nick_zanyavshego", None)
        parsing_status = request.POST.get("parsing_status", None)
        oplata_status_str = request.POST.get("oplata_status", "")

        if "," in korean_price:
            korean_price = korean_price.replace(",", ".")

        if "," in uchety_obschee_za_razbor:
            uchety_obschee_za_razbor = uchety_obschee_za_razbor.replace(",", ".")

        if "," in price_v_tenge_bez_uchetov:
            price_v_tenge_bez_uchetov = price_v_tenge_bez_uchetov.replace(",", ".")

        if oplata_status_str == "on":
            oplata_status = True
        else:
            oplata_status = False

        if card_name is None:
            return render(request, "django_salary/components/error.html", context={"error": f"card_name is None"})

        if korean_price is None:
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price is None"})

        if uchety_obschee_za_razbor is None:
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor is None"})

        if price_v_tenge_bez_uchetov is None:
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov is None"})

        if parsing_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

        if nick_zanyavshego is None:
            return render(request, "django_salary/components/error.html", context={"error": f"nick_zanyavshego is None"})

        if oplata_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"oplata_status is None"})

        # Проверка, чтобы пустые данные не приходили

        if card_name == "":
            return render(request, "django_salary/components/error.html", context={"error": f"card_name пусто"})

        if korean_price == "":
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price пусто"})

        if uchety_obschee_za_razbor == "":
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor пусто"})

        if price_v_tenge_bez_uchetov == "":
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov пусто"})

        if nick_zanyavshego == "":
            return render(request, "django_salary/components/error.html", context={"error": f"nick_zanyavshego пусто"})

        if oplata_status == "":
            return render(request, "django_salary/components/error.html", context={"error": f"oplata_status пусто"})

        order_obj = models.Orders.objects.get(id=pk_id)

        if not user.is_superuser:
            if order_obj.base_order.author != user:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Системная ошибка: Order не принадлежит Вам"})

        flag_save = False

        card_name_old = None

        if card_name != order_obj.card_name:
            card_name_old = order_obj.card_name
            order_obj.card_name = card_name
            flag_save = True

        # if korean_price != order_obj.korean_price:
        #     korean_price_old = float(order_obj.korean_price)
        #     order_obj.korean_price = korean_price
        #     flag_save = True

        korean_price_old = None

        if Decimal(float(korean_price)) != order_obj.korean_price:
            korean_price_old = float(order_obj.korean_price)
            order_obj.korean_price = Decimal(float(korean_price))
            flag_save = True

        price_v_tenge_bez_uchetov_old = None

        if Decimal(float(price_v_tenge_bez_uchetov)) != order_obj.price_v_tenge_bez_uchetov:
            price_v_tenge_bez_uchetov_old = float(order_obj.price_v_tenge_bez_uchetov)
            order_obj.price_v_tenge_bez_uchetov = Decimal(float(price_v_tenge_bez_uchetov))
            flag_save = True

        uchety_obschee_za_razbor_old = None

        if Decimal(float(uchety_obschee_za_razbor)) != order_obj.uchety_obschee_za_razbor:
            uchety_obschee_za_razbor_old = float(order_obj.uchety_obschee_za_razbor)
            order_obj.uchety_obschee_za_razbor = Decimal(float(uchety_obschee_za_razbor))
            flag_save = True

        nick_zanyavshego_old = None

        if nick_zanyavshego != order_obj.nick_zanyavshego:
            nick_zanyavshego_old = order_obj.nick_zanyavshego
            order_obj.nick_zanyavshego = nick_zanyavshego
            flag_save = True

        parsing_status_old = None

        if parsing_status != order_obj.parsing_status:
            parsing_status_old = order_obj.parsing_status
            order_obj.parsing_status = parsing_status
            flag_save = True

        oplata_status_old = None

        if oplata_status != order_obj.oplata_status:
            oplata_status_old = "Оплачено" if order_obj.oplata_status else "Не Оплачено"
            order_obj.oplata_status = oplata_status
            flag_save = True

        if flag_save:
            korean_price = float(korean_price)
            price_v_tenge_bez_uchetov = float(price_v_tenge_bez_uchetov)
            uchety_obschee_za_razbor = float(uchety_obschee_za_razbor)

            if user.is_superuser:
                kurs_obmena = cache(key=f"parsing_kurs_obmena_cache", function_queryset=lambda: parsing_kurs_obmena_cache())
            else:
                kurs_obmena = KURS_OBMENA

            price_v_tenge_po_kursu = korean_price * 10000 / kurs_obmena

            pribyl = price_v_tenge_bez_uchetov - price_v_tenge_po_kursu

            itogo_po_razboru = price_v_tenge_bez_uchetov + uchety_obschee_za_razbor

            userprofiles = models.UserProfile.objects.filter(user=user)

            if len(userprofiles) == 0 or len(userprofiles) > 1:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"UserProfile Пользователя {user.username} не найдено или больше одного"})

            userprofile = userprofiles[0]

            if userprofile.zp is None or userprofile.zp == 0:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Зарплата у Пользователя {user.username} не установлена."})

            zarplata = pribyl * userprofile.zp / 100

            order_obj.kurs_obmena = Decimal(kurs_obmena)
            order_obj.price_v_tenge_po_kursu = Decimal(price_v_tenge_po_kursu)
            order_obj.pribyl = Decimal(pribyl)
            order_obj.itogo_po_razboru = Decimal(itogo_po_razboru)
            order_obj.zarplata = Decimal(zarplata)

            order_obj.save()

            text = f"Владелец: {order_obj.base_order.author.username} Номер разбора: {order_obj.base_order.parsing_numeration} |"
            if card_name_old is not None:
                text += f"card_name: {card_name_old} -> {card_name} |"
            if korean_price_old is not None:
                text += f"korean_price: {korean_price_old} -> {korean_price} |"
            if price_v_tenge_bez_uchetov_old is not None:
                text += f"price_v_tenge_bez_uchetov: {price_v_tenge_bez_uchetov_old} -> {price_v_tenge_bez_uchetov} |"
            if uchety_obschee_za_razbor_old is not None:
                text += f"uchety_obschee_za_razbor: {uchety_obschee_za_razbor_old} -> {uchety_obschee_za_razbor} |"
            if nick_zanyavshego_old is not None:
                text += f"nick_zanyavshego: {nick_zanyavshego_old} -> {nick_zanyavshego} |"
            if parsing_status_old is not None:
                text += f"parsing_status: {parsing_status_old} -> {parsing_status} |"
            if oplata_status_old is not None:
                text += f"oplata_status: {oplata_status_old} -> {'Оплачено' if oplata_status else 'Не Оплачено'} |"
            text = text[:-2]

            models.ActivityLoggingModel.objects.create(
                username=user.username,
                myself=user == order_obj.base_order.author,
                activity="order_update",
                text=text,
            )

            update_cache(key=f"baseorder_detail_{order_obj.base_order.parsing_numeration}_{user.username}",
                         function_queryset=lambda: order_list_cache(order_obj.base_order))

            if order_obj.base_order.author != user and user.is_superuser:
                # print("order_register: BaseOrder detail обновлено")
                update_cache(key=f"baseorder_detail_{order_obj.base_order.parsing_numeration}_{order_obj.base_order.author.username}",
                             function_queryset=lambda: order_list_cache(order_obj.base_order))

        baseorder_pk = order_obj.base_order.parsing_numeration

        return redirect("baseorder_detail", baseorder_pk)


@logging
def order_delete(request: HttpRequest, pk_id: int):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        order_obj = models.Orders.objects.get(id=pk_id)

        if not user.is_superuser:
            if order_obj.base_order.author != user:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Системная ошибка: Order не принадлежит Вам"})
        baseorder_pk = order_obj.base_order.parsing_numeration
        author = order_obj.base_order.author
        order_obj.delete()
        models.ActivityLoggingModel.objects.create(
            username=user.username,
            myself=user == author,
            activity="order_delete",
            text=f"Владелец: {author.username} Номер разбора: {order_obj.base_order.parsing_numeration}",
        )
        update_cache(key=f"baseorder_detail_{order_obj.base_order.parsing_numeration}_{user.username}",
                     function_queryset=lambda: order_list_cache(order_obj.base_order))
        if order_obj.base_order.author != user and user.is_superuser:
            # print("order_delete: BaseOrder detail обновлено")
            update_cache(key=f"baseorder_detail_{order_obj.base_order.parsing_numeration}_{order_obj.base_order.author.username}",
                         function_queryset=lambda: order_list_cache(order_obj.base_order))
            update_cache(key=f"baseorder_list_{order_obj.base_order.author.username}", function_queryset=lambda: baseorder_list_cache(order_obj.base_order.author))
        return redirect("baseorder_detail", baseorder_pk)


@logging
def order_list_for_staff(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if not user.is_staff:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не staff"})
        base_orders = models.BaseOrders.objects.all()
        result = []
        if len(base_orders) != 0:
            for base_order in base_orders:
                order_objs = models.Orders.objects.filter(base_order=base_order)
                index = 1
                for order_obj in order_objs:
                    dict_tmp = {
                        "id": order_obj.id,
                        # "order_numeration": order_obj.order_numeration,
                        "order_numeration": index,
                        "author": order_obj.base_order.author.username,
                        "parsing_date": order_obj.base_order.parsing_date.strftime('%d.%m.%Y'),
                        "parsing_numeration": order_obj.base_order.parsing_numeration,
                        "band_or_performer": order_obj.base_order.band_or_performer,
                        "card_name": order_obj.card_name,
                        "parsing_status": order_obj.parsing_status,
                        "nick_zanyavshego": order_obj.nick_zanyavshego,
                    }
                    index += 1
                    result.append(dict_tmp)
        return render(request, "django_salary/order_list_for_staff.html",
                      context={"orders": result})


@logging
def order_update_for_staff(request: HttpRequest, pk_id: int):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if not user.is_staff:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не staff"})
        order_obj = models.Orders.objects.get(id=pk_id)
        result = {
            "parsing_status": order_obj.parsing_status,
        }
        return render(request, "django_salary/order_update_for_staff.html", context={"order_obj": result, "pk_id": pk_id})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не авторизованы"})
        if not user.is_staff:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Вы не staff"})
        parsing_status = request.POST.get("parsing_status", None)

        if parsing_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

        order_obj = models.Orders.objects.get(id=pk_id)

        if parsing_status != order_obj.parsing_status:
            parsing_status_old = order_obj.parsing_status
            order_obj.parsing_status = parsing_status
            order_obj.save()
            models.ActivityLoggingModel.objects.create(
                username=user.username,
                myself=user == order_obj.base_order.author,
                activity="order_update_for_staff",
                text=f"Владелец: {order_obj.base_order.author.username} "
                     f"Номер разбора: {order_obj.base_order.parsing_numeration} | parsing_status: {parsing_status_old} -> {parsing_status}",
            )
            update_cache(key=f"baseorder_detail_{order_obj.base_order.parsing_numeration}_{order_obj.base_order.author.username}",
                         function_queryset=lambda: order_list_cache(order_obj.base_order))

        return redirect("order_list_for_staff")


@logging
def user_statistic(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')

        date_from_filter = request.GET.get("date_from", "")
        date_to_filter = request.GET.get("date_to", "")
        oplata_status_filter = request.GET.get("oplata_status", "")
        oplata_status_flag = False

        list_of_username = []

        user_name = ""

        if user.is_superuser:
            user_name = request.GET.get("user_name", "")
            if user_name != "":
                user = User.objects.get(username=user_name)
            all_users = User.objects.all()
            for elem_all_users in all_users:
                if elem_all_users.username != "admin":
                    list_of_username.append(elem_all_users.username)

        if oplata_status_filter == "on":
            oplata_status_flag = True

        date_now = datetime.now()

        date_from = ""
        date_to = ""

        if date_from_filter != "" and date_to_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            if date_from >= date_to:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Неверно введены Дата от. Дата от является больше, чем Дата до"})

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__gte=date_from, parsing_date__lte=date_to)

        elif date_from_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__gte=date_from)

        elif date_to_filter != "":
            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__lte=date_to)
        else:
            base_orders = models.BaseOrders.objects.filter(author=user)

        result = []
        zarplata_sum = 0
        if len(base_orders) != 0:
            for base_order in base_orders:
            # base_order = base_orders[0]
                if oplata_status_flag:
                    order_objs = models.Orders.objects.filter(base_order=base_order, zarplata_status=False)
                else:
                    order_objs = models.Orders.objects.filter(base_order=base_order)

                # print(order_objs)
                index = 1
                for order_obj in order_objs:
                    dict_tmp = {
                        "id": order_obj.id,
                        # "order_numeration": order_obj.order_numeration,
                        "order_numeration": index,
                        "author": order_obj.base_order.author.username,
                        "parsing_date": order_obj.base_order.parsing_date.strftime('%d.%m.%Y'),
                        "parsing_numeration": order_obj.base_order.parsing_numeration,
                        "band_or_performer": order_obj.base_order.band_or_performer,
                        "card_name": order_obj.card_name,
                        # "korean_price": order_obj.korean_price,
                        # "pribyl": order_obj.pribyl,
                        # "uchety_obschee_za_razbor": order_obj.uchety_obschee_za_razbor,
                        "zarplata": order_obj.zarplata,
                        # "track_code": order_obj.base_order.track_code,
                        "parsing_status": order_obj.parsing_status,
                        # "seller_nick": order_obj.base_order.seller_nick,
                        "zarplata_status": "-" if order_obj.parsing_status == "Возврат" else order_obj.zarplata_status,
                        # "nick_zanyavshego": order_obj.nick_zanyavshego,
                        # "oplata_status": order_obj.oplata_status,
                    }
                    index += 1
                    if order_obj.parsing_status != "Возврат":
                        zarplata_sum += float(order_obj.zarplata)
                    result.append(dict_tmp)
        return render(request, "django_salary/user_statistic.html",
                      context={"orders": result, "zarplata_sum": zarplata_sum,
                               "oplata_status": oplata_status_flag, "date_now": date_now.strftime("%Y-%m-%d"),
                               "date_from": "" if date_from == "" else date_from.strftime("%Y-%m-%d"),
                               "date_to": "" if date_to == "" else date_to.strftime("%Y-%m-%d"),
                               "length_result": len(result), "list_of_username": list_of_username, "user_name": user_name})


@logging
def zp_bool_change(request: HttpRequest, pk_id: int):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if not user.is_superuser:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Недостаточно прав."})
        order_objs = models.Orders.objects.filter(id=pk_id)
        if len(order_objs) == 0 or len(order_objs) < 1:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Orders не найдено или больше одного"})
        order_obj = order_objs[0]
        zarplata_status_old = "Оплачено" if order_obj.zarplata_status else "Не Оплачено"

        if zarplata_status_old == "Оплачено":
            zarplata_status = "Не Оплачено"
        else:
            zarplata_status = "Оплачено"

        if order_obj.zarplata_status:
            order_obj.zarplata_status = False
        else:
            order_obj.zarplata_status = True
        order_obj.save()
        models.ActivityLoggingModel.objects.create(
            username=user.username,
            myself=user == order_obj.base_order.author,
            activity="zp_bool_change",
            text=f"Владелец: {order_obj.base_order.author.username} "
                 f"Номер разбора: {order_obj.base_order.parsing_numeration} | "
                 f"zarplata_status: {zarplata_status_old} -> {zarplata_status}",
        )
        # return redirect('user_statistic')
        path = request.path
        # print(f"PATH = {path}")
        return redirect(f'/orders/statistic/?user_name={order_obj.base_order.author.username}')


@logging
def download_excel_statistic(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        # date_from_filter = request.GET.get("date_from", "")
        # date_to_filter = request.GET.get("date_to", "")
        # oplata_status_filter = request.GET.get("oplata_status", "")
        # oplata_status_flag = False
        #
        # if oplata_status_filter == "on":
        #     oplata_status_flag = True
        #
        # if date_from_filter != "" and date_to_filter != "":
        #     year_date_from = int(date_from_filter.split("-")[0])
        #     month_date_from = int(date_from_filter.split("-")[1])
        #     day_date_from = int(date_from_filter.split("-")[2])
        #     date_from = datetime(year_date_from, month_date_from, day_date_from)
        #
        #     year_date_to = int(date_to_filter.split("-")[0])
        #     month_date_to = int(date_to_filter.split("-")[1])
        #     day_date_to = int(date_to_filter.split("-")[2])
        #     date_to = datetime(year_date_to, month_date_to, day_date_to)
        #
        #     if date_from >= date_to:
        #         return render(request, "django_salary/components/error.html",
        #                       context={"error": f"Неверно введены Дата от. Дата от является больше, чем Дата до"})
        #
        #     base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from, parsing_date__lte=date_to)
        #
        # elif date_from_filter != "":
        #     year_date_from = int(date_from_filter.split("-")[0])
        #     month_date_from = int(date_from_filter.split("-")[1])
        #     day_date_from = int(date_from_filter.split("-")[2])
        #     date_from = datetime(year_date_from, month_date_from, day_date_from)
        #
        #     base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from)
        #
        # elif date_to_filter != "":
        #     year_date_to = int(date_to_filter.split("-")[0])
        #     month_date_to = int(date_to_filter.split("-")[1])
        #     day_date_to = int(date_to_filter.split("-")[2])
        #     date_to = datetime(year_date_to, month_date_to, day_date_to)
        #
        #     base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__lte=date_to)
        # else:
        base_orders = models.BaseOrders.objects.filter(author=request.user)

        rows = []
        if len(base_orders) != 0:
            base_order = base_orders[0]
            order_objs = models.Orders.objects.filter(base_order=base_order)
            index = 1
            for order_obj in order_objs:
                if order_obj.zarplata_status:
                    zarplata_status = "Выплачено"
                else:
                    zarplata_status = "Не Выплачено"

                if order_obj.oplata_status:
                    oplata_status = "Оплачено"
                else:
                    oplata_status = "Не Оплачено"

                result_tmp = [index, order_obj.base_order.parsing_date.strftime("%d/%m/%Y"),
                              order_obj.base_order.parsing_numeration,
                              order_obj.base_order.band_or_performer, order_obj.card_name, order_obj.korean_price,
                              order_obj.price_v_tenge_bez_uchetov,
                              order_obj.pribyl, order_obj.uchety_obschee_za_razbor, float(order_obj.zarplata), order_obj.base_order.track_code,
                              order_obj.parsing_status, order_obj.base_order.seller_nick, zarplata_status,
                              order_obj.nick_zanyavshego, oplata_status]
                index += 1
                rows.append(result_tmp)

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="data_of_user_{request.user.username}.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Users Data')  # this will make a sheet named Users Data

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Номер записи', 'Дата разбора', 'Номер разбора', 'Группа/Исполнитель', 'Название карт', 'Цена каждой карты в кор. ценах',
                   'Цена в тенге (без учетов)', 'Прибыль', 'Учеты (общее за разбор 1900)', 'Зарплата', 'Трек-код посылки', 'Статус разбора',
                   'Ник продавца', 'Статус зарплаты', 'Ник, того кто занял', 'Статус оплаты']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)  # at 0 row 0 column

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        # rows = User.objects.all().values_list('username', 'first_name', 'last_name', 'email')
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)

        return response


@logging
def get_plot(request: HttpRequest):
    if request.method == "GET":
        user = request.user

        if not user.is_authenticated:
            return redirect('profile_login')

        date_from_filter = request.GET.get("date_from", "")
        date_to_filter = request.GET.get("date_to", "")

        list_of_username = []

        user_name = ""

        if user.is_superuser:
            user_name = request.GET.get("user_name", "")
            if user_name != "":
                user = User.objects.get(username=user_name)
            all_users = User.objects.all()
            for elem_all_users in all_users:
                if elem_all_users.username != "admin":
                    list_of_username.append(elem_all_users.username)

        date_now = datetime.now()

        date_from = ""
        date_to = ""

        if date_from_filter != "" and date_to_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            if date_from >= date_to:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Неверно введены Дата от. Дата от является больше, чем Дата до",
                                       "url_back": "get_plot"})

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__gte=date_from, parsing_date__lte=date_to)

        elif date_from_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__gte=date_from)

        elif date_to_filter != "":
            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            base_orders = models.BaseOrders.objects.filter(author=user, parsing_date__lte=date_to)
        else:
            base_orders = models.BaseOrders.objects.filter(author=user)

        boolean_empty = False

        if len(base_orders) == 0:
            boolean_empty = True

        dict_baseorders = {}
        for base_order in base_orders:
            if base_order.parsing_date not in dict_baseorders:
                dict_baseorders[base_order.parsing_date] = 1
            else:
                dict_baseorders[base_order.parsing_date] += 1

        # print(dict_baseorders)

        list_x_not_sorted = list(dict_baseorders.keys())
        # print(list_x_not_sorted)
        list_x_sorted = sorted(list_x_not_sorted)
        # print(list_x_sorted)

        list_y_sorted = []
        for elem_list_x_sorted in list_x_sorted:
            list_y_sorted.append(dict_baseorders[elem_list_x_sorted])

        # Создание графика с использованием Plotly
        # x = [1, 2, 3, 4, 5]
        # y = [2, 4, 6, 8, 10]
        # y = [1, 2, 3]
        # x = [date_now_1, date_now_2, date_now]
        if not boolean_empty:
            data = [go.Scatter(x=list_x_sorted, y=list_y_sorted)]
            layout = go.Layout(title='График', xaxis=dict(title='X'), yaxis=dict(title='Y'))
            fig = go.Figure(data=data, layout=layout)
            graph_html = opy.plot(fig, auto_open=False, output_type='div')
        else:
            graph_html = None

        # Передача HTML-кода графика в контексте шаблона Jinja2
        context = {'graph_html': graph_html, "boolean_empty": boolean_empty,
                   "date_now": date_now.strftime("%Y-%m-%d"),
                   "date_from": "" if date_from == "" else date_from.strftime("%Y-%m-%d"),
                   "date_to": "" if date_to == "" else date_to.strftime("%Y-%m-%d"), "list_of_username": list_of_username,
                   "user_name": user_name}
        return render(request, 'django_salary/graph.html', context)


@logging
def order_list_for_unregistered(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        base_orders = models.BaseOrders.objects.all()
        result = []
        if len(base_orders) != 0:
            for base_order in base_orders:
                order_objs = models.Orders.objects.filter(base_order=base_order)
                index = 1
                for order_obj in order_objs:
                    dict_tmp = {
                        # "id": order_obj.id,
                        # "order_numeration": order_obj.order_numeration,
                        "order_numeration": index,
                        "author": order_obj.base_order.author.username,
                        "parsing_date": order_obj.base_order.parsing_date.strftime('%d.%m.%Y'),
                        "parsing_numeration": order_obj.base_order.parsing_numeration,
                        "band_or_performer": order_obj.base_order.band_or_performer,
                        "card_name": order_obj.card_name,
                        "parsing_status": order_obj.parsing_status,
                        "nick_zanyavshego": order_obj.nick_zanyavshego,
                    }
                    index += 1
                    result.append(dict_tmp)

        return render(request, "django_salary/order_list_for_unregistered.html",
                      context={"orders": result})


@logging
def raspredelenie_zp(request: HttpRequest):
    if request.method == "GET":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if not user.is_superuser:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Недостаточно прав."})

        return render(request, "django_salary/raspredelenie_zp.html",
                      context={"title": "Для просмотра распределения Зарплаты введите пароль",
                               "boolean": True})
    elif request.method == "POST":
        user = request.user
        if not user.is_authenticated or not user.is_superuser:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Недостаточно прав."})
        password = request.POST.get("password", "")

        check_password = user.check_password(password)

        if not check_password:
            title = "Введенный пароль неверный."
            return render(request, "django_salary/raspredelenie_zp.html",
                          context={"title": title, "boolean": check_password})
        else:
            all_userprofiles = models.UserProfile.objects.all()
            return render(request, "django_salary/list_of_zp.html", context={"all_userprofiles": all_userprofiles})


@logging
def change_raspredelenie_zp(request: HttpRequest, pk_id: int):
    if request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return redirect('profile_login')
        if not user.is_superuser:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"У вас нет доступа. Недостаточно прав."})
        zp = request.POST.get("zp", "")
        userprofile = models.UserProfile.objects.get(id=pk_id)
        if userprofile.zp != zp:
            zp_old = userprofile.zp
            userprofile.zp = zp
            userprofile.save()
            models.ActivityLoggingModel.objects.create(
                username=user.username,
                myself=False,
                activity="change_raspredelenie_zp",
                text=f"Владелец: {userprofile.user.username} | userprofile.zp: {zp_old} -> {zp}",
            )
        all_userprofiles = models.UserProfile.objects.all()
        return render(request, "django_salary/list_of_zp.html", context={"all_userprofiles": all_userprofiles})
        # return redirect('salary' all_userprofiles)


