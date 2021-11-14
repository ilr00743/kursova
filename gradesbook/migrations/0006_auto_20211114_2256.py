# Generated by Django 2.2.6 on 2021-11-14 20:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gradesbook', '0005_auto_20211114_2245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolclass',
            name='name',
            field=models.CharField(help_text='Число + буква нижнього реєстру, напр.: 1a', max_length=10),
        ),
        migrations.AlterField(
            model_name='schoolclass',
            name='unique_code',
            field=models.CharField(help_text='Формат: назва класу + рік навчання, наприклад: 1b2019', max_length=10, unique=True, validators=[django.core.validators.RegexValidator('^[1-10]{1}[a-z]{1}[0-9]{4}$')]),
        ),
    ]
