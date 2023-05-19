from django_salary import models
from django.utils import timezone
import csv
from datetime import datetime, timedelta


def my_cron_job():
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
