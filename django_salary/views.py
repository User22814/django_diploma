from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest, FileResponse
from django.shortcuts import render, redirect
import re
from django_salary import models
from decimal import Decimal
from datetime import datetime, timedelta
from openpyxl import Workbook
from django.http import HttpResponse
import xlwt


KURS_RASCHETA = 2.8844
# Create your views here.
# КЭШ
# С помощью библиотеки для визуализации данных выводить график статистики
# Вывод в excel фильтрованных данных

ZP_dict = {"admin": 0.3}

def profile_register(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "django_salary/profile_register.html", context={})
    elif request.method == "POST":
        name = request.POST["name"]
        username = request.POST["username"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            # raise Exception("incorrect password")
            return render(request, "django_salary/components/error.html",
                          context={"error": f"password1 и password2 не одинаковы"})

        pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])[A-Za-z\d!@#$%^&*()_+]{8,}$'

        if not re.match(pattern, password1):
            # raise Exception("Пароль должен содержать минимум 8 символов, одну заглавную, одну строчную букву и одно число")
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Пароль должен содержать минимум 8 символов, одну заглавную, одну строчную букву и одно число"})

        user = User.objects.create_user(
            username=username,
            password=password1
        )

        models.UserProfile.objects.create(
            user=user,
            name=name
        )
        return redirect("profile_login")


def profile_login(request):
    if request.method == 'GET':
        return render(request, 'django_salary/profile_login.html', context={})
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is None:
            # raise Exception("incorrect password")
            return render(request, "django_salary/components/error.html",
                          context={"error": f"Введенный пароль неверный"})
        login(request, user)
        return redirect('baseorder_list')


def profile_logout(request):
    logout(request)
    return redirect('profile_login')


def baseorder_list(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        baseorders = models.BaseOrders.objects.filter(author=request.user)
        result = []
        for baseorder in baseorders:
            dict_tmp = {
                "baseorder_numeration": baseorder.baseorder_numeration,
                "author": baseorder.author.username,
                "parsing_numeration": baseorder.parsing_numeration,
                "parsing_date": baseorder.parsing_date.strftime('%d.%m.%Y'),
                "count": baseorder.get_count_of_orders(),
                "band_or_performer": baseorder.band_or_performer,
                "track_code": baseorder.track_code,
                "parsing_status": baseorder.parsing_status,
                "seller_nick": baseorder.seller_nick,
            }
            result.append(dict_tmp)
        return render(request, "django_salary/baseorder_list.html", context={"orders": result})


def baseorder_detail(request: HttpRequest, pk) -> HttpResponse:
    if request.method == "GET":
        base_orders = models.BaseOrders.objects.filter(parsing_numeration=pk, author=request.user)
        if len(base_orders) == 0 or len(base_orders) > 1:
            return render(request, "django_salary/components/error.html",
                          context={"error": f"BaseOrder с номером {pk} у Пользователя {request.user.username} нет или больше одного"})
        base_order = base_orders[0]
        order_objs = models.Orders.objects.filter(base_order=base_order)  # (1, 'Электроника', 'electro')
        result = []
        for order_obj in order_objs:
            dict_tmp = {
                "id": order_obj.id,
                "order_numeration": order_obj.order_numeration,
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
                "parsing_status": order_obj.base_order.parsing_status,
                "seller_nick": order_obj.base_order.seller_nick,
                "zarplata_status": order_obj.zarplata_status,
                "nick_zanyavshego": order_obj.nick_zanyavshego,
                "oplata_status": order_obj.oplata_status,
            }
            result.append(dict_tmp)
            # print(order_obj.id)
            # print(type(order_obj.id))
        # print(pk)
        # print(type(pk))
        return render(request, "django_salary/order_list.html", context={"order_objs": result, "baseorder_pk": pk, "base_order": base_order})


def baseorder_update(request, pk):
    if request.method == "GET":
        user = request.user
        baseorder_obj = models.BaseOrders.objects.get(author=user, parsing_numeration=pk)
        result = {
            "baseorder_numeration": baseorder_obj.baseorder_numeration,
            "parsing_date": baseorder_obj.parsing_date.strftime('%Y-%m-%d'),
            "parsing_numeration": baseorder_obj.parsing_numeration,
            "band_or_performer": baseorder_obj.band_or_performer,
            "track_code": baseorder_obj.track_code,
            "parsing_status": baseorder_obj.parsing_status,
            "seller_nick": baseorder_obj.seller_nick,
        }
        return render(request, "django_salary/baseorder_update.html", context={"baseorder_obj": result})
    elif request.method == "POST":
        parsing_date = request.POST.get("parsing_date", None)
        parsing_numeration = request.POST.get("parsing_numeration", None)
        band_or_performer = request.POST.get("band_or_performer", None)
        track_code = request.POST.get("track_code", None)
        parsing_status = request.POST.get("parsing_status", None)
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

        if parsing_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

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

        baseorder_obj = models.BaseOrders.objects.get(author=user, parsing_numeration=pk)

        flag_save = False

        if parsing_date != baseorder_obj.parsing_date:
            baseorder_obj.parsing_date = parsing_date
            flag_save = True

        if parsing_numeration != baseorder_obj.parsing_numeration:
            baseorder_obj.parsing_numeration = parsing_numeration
            flag_save = True

        if band_or_performer.lower().strip() != baseorder_obj.band_or_performer:
            baseorder_obj.band_or_performer = band_or_performer.lower().strip()
            flag_save = True

        if track_code != baseorder_obj.track_code:
            baseorder_obj.track_code = track_code
            flag_save = True

        if parsing_status != baseorder_obj.parsing_status:
            baseorder_obj.parsing_status = parsing_status
            flag_save = True

        if seller_nick != baseorder_obj.seller_nick:
            baseorder_obj.seller_nick = seller_nick
            flag_save = True

        if flag_save:
            baseorder_obj.save()

        # models.BaseOrders.objects.create(
        #     baseorder_numeration=next_numeration,
        #     author=user,
            # parsing_date=parsing_date,
            # parsing_numeration=int(parsing_numeration),
            # band_or_performer=band_or_performer.lower().strip(),
            # track_code=track_code,
            # parsing_status=parsing_status,
            # seller_nick=seller_nick,
        # )

        # return redirect("profile_login")
        return redirect("baseorder_list")
        # return redirect("order_register")


def baseorder_delete(request, pk):
    if request.method == "GET":
        user = request.user
        baseorder_obj = models.BaseOrders.objects.get(author=user, parsing_numeration=pk)
        baseorder_obj.delete()
        return redirect("baseorder_list")


def tovar_by_user(request, username: str):
    user_obj = User.objects.get(username=username)
    tovars = models.Tovar.objects.filter(seller=user_obj)
    return render(request, "django_salary/category.html", context={"tovars": tovars})


def tovar_detail(request):
    return HttpResponse("<h1>profile_register</h1>")


def baseorder_register(request):
    if request.method == "GET":
        baseorder_objs = models.BaseOrders.objects.all()
        if len(baseorder_objs) != 0:
            last_baseorder_obj = baseorder_objs.last()
            last_numeration = last_baseorder_obj.parsing_numeration
        else:
            last_numeration = 0
        return render(request, "django_salary/baseorder_create.html", context={"last_numeration": last_numeration})
    elif request.method == "POST":
        parsing_date = request.POST.get("parsing_date", None)
        parsing_numeration = request.POST.get("parsing_numeration", None)
        band_or_performer = request.POST.get("band_or_performer", None)
        track_code = request.POST.get("track_code", None)
        parsing_status = request.POST.get("parsing_status", None)
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

        if parsing_status is None:
            return render(request, "django_salary/components/error.html", context={"error": f"parsing_status is None"})

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

        # list_of_numeration = []

        user = request.user

        baseorder_objs_all = models.BaseOrders.objects.all()

        baseorder_obj_all_last = baseorder_objs_all.last()

        if int(parsing_numeration) <= baseorder_obj_all_last.parsing_numeration:
            return render(request, "django_salary/components/error.html", context={"error": f"Номер разбора не может быть меньше или равно {baseorder_obj_all_last.parsing_numeration}"})

        baseorder_objs = baseorder_objs_all.filter(author=user)

        # next_numeration = 0

        if len(baseorder_objs) == 0:
            next_numeration = 1
        else:
            # for order_obj in baseorder_objs:
            #     list_of_numeration.append(order_obj.baseorder_numeration)
            # next_numeration = max(list_of_numeration) + 1
            next_numeration = baseorder_objs.last().baseorder_numeration + 1

        models.BaseOrders.objects.create(
            baseorder_numeration=next_numeration,
            author=user,
            parsing_date=parsing_date,
            parsing_numeration=int(parsing_numeration),
            band_or_performer=band_or_performer.lower().strip(),
            track_code=track_code,
            parsing_status=parsing_status,
            seller_nick=seller_nick,
        )

        # return redirect("profile_login")
        return redirect("baseorder_list")
        # return redirect("order_register")


def order_register(request, baseorder_pk: int):
    if request.method == "GET":
        return render(request, "django_salary/order_create.html", context={"baseorder_pk": baseorder_pk})
    elif request.method == "POST":
        # print(request.POST)
        # parsing_date = request.POST.get("parsing_date", None)
        # parsing_numeration = request.POST.get("parsing_numeration", None)
        # band_or_performer = request.POST.get("band_or_performer", None)
        card_name = request.POST.get("card_name", None)
        korean_price = request.POST.get("korean_price", None)
        uchety_obschee_za_razbor = request.POST.get("uchety_obschee_za_razbor", None)
        price_v_tenge_bez_uchetov = request.POST.get("price_v_tenge_bez_uchetov", None)
        # track_code = request.POST.get("track_code", None)
        # seller_nick = request.POST.get("seller_nick", None)
        nick_zanyavshego = request.POST.get("nick_zanyavshego", None)
        oplata_status = request.POST.get("oplata_status", False)

        if oplata_status == "true":
            oplata_status = True

        if card_name is None:
            return render(request, "django_salary/components/error.html", context={"error": f"card_name is None"})

        if korean_price is None:
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price is None"})

        if price_v_tenge_bez_uchetov is None:
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov is None"})

        if uchety_obschee_za_razbor is None:
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor is None"})

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

        if nick_zanyavshego == "":
            return render(request, "django_salary/components/error.html", context={"error": f"nick_zanyavshego пусто"})

        if oplata_status == "":
            return render(request, "django_salary/components/error.html", context={"error": f"oplata_status пусто"})

        user = request.user

        baseorder_obj = models.BaseOrders.objects.get(author=user, baseorder_numeration=baseorder_pk)

        order_objs = models.Orders.objects.filter(base_order=baseorder_obj)

        next_numeration = 0

        if len(order_objs) != 0:
            # for order_obj in order_objs:
            #     list_of_numeration.append(order_obj.order_numeration)
            next_numeration = order_objs.last().order_numeration + 1
        elif len(order_objs) == 0:
            next_numeration = 1

        korean_price = float(korean_price)
        price_v_tenge_bez_uchetov = float(price_v_tenge_bez_uchetov)
        uchety_obschee_za_razbor = float(uchety_obschee_za_razbor)

        price_v_tenge_po_kursu = korean_price * 10000 / KURS_RASCHETA

        pribyl = price_v_tenge_bez_uchetov - price_v_tenge_po_kursu

        itogo_po_razboru = price_v_tenge_bez_uchetov + uchety_obschee_za_razbor

        zarplata = pribyl * ZP_dict[user.username]

        models.Orders.objects.create(
            order_numeration=next_numeration,
            base_order=baseorder_obj,
            card_name=card_name.lower().strip(),
            korean_price=Decimal(korean_price),
            price_v_tenge_po_kursu=Decimal(price_v_tenge_po_kursu),
            price_v_tenge_bez_uchetov=Decimal(price_v_tenge_bez_uchetov),
            pribyl=Decimal(pribyl),
            uchety_obschee_za_razbor=Decimal(uchety_obschee_za_razbor),
            itogo_po_razboru=Decimal(itogo_po_razboru),
            zarplata=Decimal(zarplata),
            nick_zanyavshego=nick_zanyavshego,
            oplata_status=oplata_status,
        )

        return redirect("baseorder_detail", baseorder_pk)


def order_update(request, pk_id: int):
    if request.method == "GET":
        order_obj = models.Orders.objects.get(id=pk_id)
        result = {
            "card_name": order_obj.card_name,
            "korean_price": float(order_obj.korean_price),
            "uchety_obschee_za_razbor": int(float(order_obj.uchety_obschee_za_razbor)),
            "price_v_tenge_bez_uchetov": int(float(order_obj.price_v_tenge_bez_uchetov)),
            "nick_zanyavshego": order_obj.nick_zanyavshego,
            "oplata_status": order_obj.oplata_status,
        }
        # print(result['korean_price'])
        # print(type(result['korean_price']))
        return render(request, "django_salary/order_update.html", context={"pk_id": pk_id, "order_obj": result})
    elif request.method == "POST":
        card_name = request.POST.get("card_name", None)
        korean_price = request.POST.get("korean_price", None)
        uchety_obschee_za_razbor = request.POST.get("uchety_obschee_za_razbor", None)
        price_v_tenge_bez_uchetov = request.POST.get("price_v_tenge_bez_uchetov", None)
        nick_zanyavshego = request.POST.get("nick_zanyavshego", None)
        oplata_status = request.POST.get("oplata_status", False)

        if "," in korean_price:
            korean_price = korean_price.replace(",", ".")

        if "," in uchety_obschee_za_razbor:
            uchety_obschee_za_razbor = uchety_obschee_za_razbor.replace(",", ".")

        if "," in price_v_tenge_bez_uchetov:
            price_v_tenge_bez_uchetov = price_v_tenge_bez_uchetov.replace(",", ".")

        if oplata_status == "true":
            oplata_status = True

        if card_name is None:
            return render(request, "django_salary/components/error.html", context={"error": f"card_name is None"})

        if korean_price is None:
            return render(request, "django_salary/components/error.html", context={"error": f"korean_price is None"})

        if uchety_obschee_za_razbor is None:
            return render(request, "django_salary/components/error.html", context={"error": f"uchety_obschee_za_razbor is None"})

        if price_v_tenge_bez_uchetov is None:
            return render(request, "django_salary/components/error.html", context={"error": f"price_v_tenge_bez_uchetov is None"})

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

        flag_save = False

        if card_name != order_obj.card_name:
            order_obj.card_name = card_name
            flag_save = True

        if korean_price != order_obj.korean_price:
            order_obj.korean_price = korean_price
            flag_save = True

        if Decimal(float(korean_price)) != order_obj.korean_price:
            order_obj.korean_price = Decimal(float(korean_price))
            flag_save = True

        if Decimal(float(price_v_tenge_bez_uchetov)) != order_obj.price_v_tenge_bez_uchetov:
            order_obj.price_v_tenge_bez_uchetov = Decimal(float(price_v_tenge_bez_uchetov))
            flag_save = True

        if Decimal(float(uchety_obschee_za_razbor)) != order_obj.uchety_obschee_za_razbor:
            order_obj.uchety_obschee_za_razbor = Decimal(float(uchety_obschee_za_razbor))
            flag_save = True

        if nick_zanyavshego != order_obj.nick_zanyavshego:
            order_obj.nick_zanyavshego = nick_zanyavshego
            flag_save = True

        if oplata_status != order_obj.oplata_status:
            order_obj.oplata_status = oplata_status
            flag_save = True

        if flag_save:
            korean_price = float(korean_price)
            price_v_tenge_bez_uchetov = float(price_v_tenge_bez_uchetov)
            uchety_obschee_za_razbor = float(uchety_obschee_za_razbor)

            price_v_tenge_po_kursu = korean_price * 10000 / KURS_RASCHETA

            pribyl = price_v_tenge_bez_uchetov - price_v_tenge_po_kursu

            itogo_po_razboru = price_v_tenge_bez_uchetov + uchety_obschee_za_razbor

            zarplata = pribyl * ZP_dict[request.user.username]

            order_obj.price_v_tenge_po_kursu = price_v_tenge_po_kursu
            order_obj.pribyl = pribyl
            order_obj.itogo_po_razboru = itogo_po_razboru
            order_obj.zarplata = zarplata

            order_obj.save()

        baseorder_pk = order_obj.base_order.baseorder_numeration

        return redirect("baseorder_detail", baseorder_pk)


def order_delete(request, pk_id: int):
    if request.method == "GET":
        order_obj = models.Orders.objects.get(id=pk_id)
        baseorder_pk = order_obj.base_order.baseorder_numeration
        order_obj.delete()
        return redirect("baseorder_detail", baseorder_pk)


def user_statistic(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        date_from_filter = request.GET.get("date_from", "")
        date_to_filter = request.GET.get("date_to", "")
        oplata_status_filter = request.GET.get("oplata_status", "")
        oplata_status_flag = False

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

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from, parsing_date__lte=date_to)

        elif date_from_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from)

        elif date_to_filter != "":
            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__lte=date_to)
        else:
            base_orders = models.BaseOrders.objects.filter(author=request.user)

        result = []
        zarplata_sum = 0
        if len(base_orders) != 0:
            base_order = base_orders[0]
            if oplata_status_flag:
                order_objs = models.Orders.objects.filter(base_order=base_order, zarplata_status=True)
            else:
                order_objs = models.Orders.objects.filter(base_order=base_order)

            # print(order_objs)
            for order_obj in order_objs:
                dict_tmp = {
                    # "id": order_obj.id,
                    "order_numeration": order_obj.order_numeration,
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
                    # "parsing_status": order_obj.base_order.parsing_status,
                    # "seller_nick": order_obj.base_order.seller_nick,
                    "zarplata_status": order_obj.zarplata_status,
                    # "nick_zanyavshego": order_obj.nick_zanyavshego,
                    # "oplata_status": order_obj.oplata_status,
                }
                zarplata_sum += float(order_obj.zarplata)
                result.append(dict_tmp)
        return render(request, "django_salary/user_statistic.html",
                      context={"orders": result, "zarplata_sum": zarplata_sum,
                               "oplata_status": oplata_status_flag, "date_now": date_now.strftime("%Y-%m-%d"),
                               "date_from": "" if date_from == "" else date_from.strftime("%Y-%m-%d"),
                               "date_to": "" if date_to == "" else date_to.strftime("%Y-%m-%d")})


def download_excel_statistic(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        date_from_filter = request.GET.get("date_from", "")
        date_to_filter = request.GET.get("date_to", "")
        oplata_status_filter = request.GET.get("oplata_status", "")
        oplata_status_flag = False

        if oplata_status_filter == "on":
            oplata_status_flag = True

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

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from, parsing_date__lte=date_to)

        elif date_from_filter != "":
            year_date_from = int(date_from_filter.split("-")[0])
            month_date_from = int(date_from_filter.split("-")[1])
            day_date_from = int(date_from_filter.split("-")[2])
            date_from = datetime(year_date_from, month_date_from, day_date_from)

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__gte=date_from)

        elif date_to_filter != "":
            year_date_to = int(date_to_filter.split("-")[0])
            month_date_to = int(date_to_filter.split("-")[1])
            day_date_to = int(date_to_filter.split("-")[2])
            date_to = datetime(year_date_to, month_date_to, day_date_to)

            base_orders = models.BaseOrders.objects.filter(author=request.user, parsing_date__lte=date_to)
        else:
            base_orders = models.BaseOrders.objects.filter(author=request.user)

        rows = []
        zarplata_sum = 0
        if len(base_orders) != 0:
            base_order = base_orders[0]
            if oplata_status_flag:
                order_objs = models.Orders.objects.filter(base_order=base_order, zarplata_status=True)
            else:
                order_objs = models.Orders.objects.filter(base_order=base_order)

            # print(order_objs)
            for order_obj in order_objs:
                if order_obj.zarplata_status:
                    zarplata_status = "Выплачено"
                else:
                    zarplata_status = "Не Выплачено"

                if order_obj.oplata_status:
                    oplata_status = "Оплачено"
                else:
                    oplata_status = "Не Оплачено"

                result_tmp = [order_obj.order_numeration, order_obj.base_order.parsing_date, order_obj.base_order.parsing_numeration,
                              order_obj.base_order.band_or_performer, order_obj.card_name, order_obj.korean_price, order_obj.price_v_tenge_bez_uchetov,
                              order_obj.pribyl, order_obj.uchety_obschee_za_razbor, float(order_obj.zarplata), order_obj.base_order.track_code,
                              order_obj.base_order.parsing_status, order_obj.base_order.seller_nick, zarplata_status,
                              order_obj.nick_zanyavshego, oplata_status]
                rows.append(result_tmp)

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="users.xls"'

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

