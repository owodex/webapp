# Generated by Django 5.1.4 on 2025-02-06 13:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_giftcarddenomination_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftCardRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('card_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.giftcardtype')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.giftcardcurrency')),
                ('denomination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.giftcarddenomination')),
                ('giftcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rates', to='app.giftcard')),
            ],
            options={
                'unique_together': {('giftcard', 'currency', 'card_type', 'denomination')},
            },
        ),
    ]
