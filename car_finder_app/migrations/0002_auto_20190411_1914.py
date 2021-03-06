# Generated by Django 2.2 on 2019-04-11 19:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('car_finder_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpiderRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('duration', models.DurationField()),
            ],
        ),
        migrations.RemoveField(
            model_name='carsaleinfo',
            name='last_synced',
        ),
        migrations.AddField(
            model_name='carsaleinfo',
            name='is_new',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='carbrand',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='country',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='carmodel',
            unique_together={('name', 'brand')},
        ),
        migrations.AlterUniqueTogether(
            name='city',
            unique_together={('name', 'country')},
        ),
        migrations.AlterUniqueTogether(
            name='generation',
            unique_together={('name', 'car_model')},
        ),
        migrations.AddField(
            model_name='carsaleinfo',
            name='last_spider_run',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='sales', to='car_finder_app.SpiderRun'),
            preserve_default=False,
        ),
    ]
