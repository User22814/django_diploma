from django.http import HttpResponse, HttpRequest
import time
from django.conf import settings
from django_salary import models
import datetime
from django.shortcuts import render

# datetime_pusk = datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
time_pusk = datetime.time(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def logging(func_controller: callable) -> any:
    def __wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        time_start_func = time.perf_counter()
        # print(_request.META.get("REMOTE_ADDR"), _request.META.get("COMPUTERNAME"), _request.META.get("USERNAME"))

        response = func_controller(request, *args, **kwargs)
        # time_stop_func = time.perf_counter()
        time_elapsed = round(time.perf_counter() - time_start_func, 5)

        print(f"{request.path}: {time_elapsed} sec")

        if request.user.username:
            user = request.user
        else:
            user = None

        if user is None:
            ip = request.META.get('REMOTE_ADDR') if request.META.get('REMOTE_ADDR') else request.META.get('HTTP_X_FORWARDED_FOR')
            models.BlackListIPModel.objects.create(
                ip=ip,
                path=request.path,
            )
            current_time = datetime.datetime.now()
            ten_minutes_ago = current_time - datetime.timedelta(minutes=10)
            len_objs_ten_minutes_ago = models.BlackListIPModel.objects.filter(created__gte=ten_minutes_ago).count()
            if len_objs_ten_minutes_ago >= 100:
                return render(request, "django_salary/components/error.html",
                              context={"error": f"Вы внесены в черный список IP"})

        # print(request.user)
        # print(response)
        # print(request.META.get('REMOTE_ADDR'))
        #
        #
        # print(username)

        # baseorder/register/
        # baseorder/update/
        # baseorder/delete/

        # orders/register/
        # orders/update/
        # orders/delete/


        # error_bool = ""
        #
        # if response.data:
        #     error_bool = response.data.get('error')
        #
        # if error_bool:
        #     error_value = response.data['error']
        #
        #     models.LoggingModel.objects.create(
        #         user=user,
        #         username=username,
        #         ip=request.META.get('REMOTE_ADDR') if request.META.get('REMOTE_ADDR') else request.META.get('HTTP_X_FORWARDED_FOR'),
        #         path=request.path,
        #         method=request.method,
        #         text=f"Error ({response.status_code}) ({time_elapsed} sec): " + str(error_value) + f"|DATA: {request.data}",
        #         # text=f"Error ({response.status_code}) ({time_elapsed} sec): " + str(error_value),
        #     )
        # else:
        #     models.LoggingModel.objects.create(
        #         user=user,
        #         username=username,
        #         ip=request.META.get('REMOTE_ADDR') if request.META.get('REMOTE_ADDR') else request.META.get('HTTP_X_FORWARDED_FOR'),
        #         path=request.path,
        #         method=request.method,
        #         text=f"Response ({response.status_code}) ({time_elapsed} sec): " + str(response.data) + f"|DATA: {request.data}",
        #         # text=f"Response ({response.status_code}) ({time_elapsed} sec): "
        #     )
        # if settings.LOGGING_TXT:
        #     file_name = datetime.datetime.now().strftime("%d-%m-%Y")
        #     text = f"\ntime: {datetime.datetime.now()} user: {request.user if request.user.username else None} ip: " \
        #            f"{request.META.get('REMOTE_ADDR') if request.META.get('REMOTE_ADDR') else request.META.get('HTTP_X_FORWARDED_FOR')} path: {request.path} method: {request.method} action: " \
        #            f"_request.action response: [{time_elapsed}]"
        #     with open(f"static/logging/{file_name}.txt", "a") as log:
        #         log.write(text)

        return response
    return __wrapper
