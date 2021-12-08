# Generated by Django 3.2.8 on 2021-11-28 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_auto_20211129_0047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemproperty',
            name='type',
            field=models.CharField(choices=[('TEXT', 'Text'), ('NUMB', 'Number'), ('BOOL', 'Boolean')], default='TEXT', max_length=4, verbose_name='type'),
        ),
    ]