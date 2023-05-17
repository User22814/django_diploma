from django.core.validators import MinValueValidator, MinLengthValidator, MaxLengthValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.ForeignKey(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='User',
        help_text='<small class="text-muted">ForeignKey</small><hr><br>',

        to=User,
        on_delete=models.CASCADE,
    )
    name = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(100), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Имя Пользователя',
        help_text='<small class="text-muted">text_field[0, 100]</small><hr><br>',

        max_length=100,
    )

    class Meta:
        app_label = "auth"
        ordering = ('id',)
        verbose_name = 'Профиль Пользователя'
        verbose_name_plural = 'Профиль Пользователей'

    def __str__(self):
        return f"{self.user}|{self.name}"


class BaseOrders(models.Model):
    baseorder_numeration = models.IntegerField(
        error_messages=False,
        primary_key=False,
        validators=[MinValueValidator(0), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Номер записи',
        help_text='<small class="text-muted">IntegerField [0, ]</small><hr><br>',
    )
    author = models.ForeignKey(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Автор',
        help_text='<small class="text-muted">ForeignKey</small><hr><br>',

        to=User,
        on_delete=models.SET_NULL,
    )
    parsing_date = models.DateField(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=timezone.now,
        verbose_name='Дата разбора',
        help_text='<small class="text-muted">DateTimeField</small><hr><br>',
    )
    parsing_numeration = models.IntegerField(
        error_messages=False,
        primary_key=False,
        validators=[MinValueValidator(0), ],
        unique=True,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Номер разбора',
        help_text='<small class="text-muted">IntegerField [0, ]</small><hr><br>',
    )
    band_or_performer = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(3000), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Группа/Исполнитель',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=3000,
    )
    track_code = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(3000), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Трек код',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=3000,
    )
    parsing_status = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(100), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Статус разбора',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=100,
    )
    seller_nick = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(3000), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Ник продавца',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=3000,
    )

    class Meta:
        app_label = "django_salary"
        ordering = ('id',)
        verbose_name = 'Базовые Заказы'
        verbose_name_plural = 'Базовые Заказы'

    def __str__(self):
        return f"{self.author}|{self.parsing_numeration}"

    def get_count_of_orders(self):
        order_objs = Orders.objects.filter(base_order=self)
        return len(order_objs)


class Orders(models.Model):
    order_numeration = models.IntegerField(
        error_messages=False,
        primary_key=False,
        validators=[MinValueValidator(0), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Номер записи',
        help_text='<small class="text-muted">IntegerField [0, ]</small><hr><br>',
    )
    base_order = models.ForeignKey(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Автор',
        help_text='<small class="text-muted">ForeignKey</small><hr><br>',

        to=BaseOrders,
        on_delete=models.CASCADE,
    )
    card_name = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(3000), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Название карты',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=3000,
    )
    korean_price = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Цена каждой карты в Корейских ценах',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    price_v_tenge_po_kursu = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Цена в тенге по курсу',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    price_v_tenge_bez_uchetov = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Цена в тенге (без учетов)',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    pribyl = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Прибыль',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    uchety_obschee_za_razbor = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Учеты (общее за разбор)',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    itogo_po_razboru = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Итого по разбору',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    zarplata = models.DecimalField(
        error_messages=False,
        primary_key=False,
        max_digits=7,
        unique=False,
        validators=[MinValueValidator(0), MaxValueValidator(100000), ],
        editable=True,
        blank=True,
        null=True,
        decimal_places=1,
        default=0.0,
        verbose_name='Зарплата',
        help_text='<small class="text-muted">DecimalField</small><hr><br>',
    )
    zarplata_status = models.BooleanField(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=False,
        default=False,
        verbose_name='Статус зарплаты',
        help_text='<small class="text-muted">BooleanField</small><hr><br>',
    )
    nick_zanyavshego = models.TextField(
        error_messages=False,
        primary_key=False,
        validators=[MinLengthValidator(0), MaxLengthValidator(3000), ],
        unique=False,
        editable=True,
        blank=True,
        null=True,
        default='',
        verbose_name='Ник того, кто занял',
        help_text='<small class="text-muted">text_field[0, 3000]</small><hr><br>',

        max_length=3000,
    )
    oplata_status = models.BooleanField(
        error_messages=False,
        primary_key=False,
        unique=False,
        editable=True,
        blank=True,
        null=False,
        default=False,
        verbose_name='Статус оплаты',
        help_text='<small class="text-muted">BooleanField</small><hr><br>',
    )

    class Meta:
        app_label = "django_salary"
        ordering = ('id',)
        verbose_name = 'Заказы'
        verbose_name_plural = 'Заказы'

    # def __str__(self):
    #     return self.name
    #
    # def get_absolute_url(self):
    #     return reverse('category_detail', args=[self.slug])


# class Tovar(models.Model):
#     title = models.CharField(verbose_name="Наименование товара", max_length=200)
#     slug = models.SlugField(verbose_name="Ссылка на товар", max_length=200, unique=True)
#     category = models.ForeignKey(Category, null=True, default=None, on_delete=models.SET_NULL)
#     seller = models.ForeignKey(User, on_delete=models.CASCADE)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     image = models.ImageField(upload_to='ads/%Y/%m/%d/', blank=True)
#     created = models.DateTimeField(default=timezone.now)
#     updated = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         app_label = "django_salary"
#         ordering = ('-created',)
#         verbose_name = 'Товар'
#         verbose_name_plural = 'Товары'
#
#     def __str__(self):
#         return self.title
#
#     def get_absolute_url(self):
#         return reverse('ad_detail', args=[self.slug])
