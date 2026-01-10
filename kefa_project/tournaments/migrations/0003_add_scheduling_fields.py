# Generated migration for automated scheduling fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0002_add_fixtures_generated'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='match_frequency',
            field=models.CharField(
                choices=[
                    ('daily', 'Daily'),
                    ('every_2_days', 'Every 2 Days'),
                    ('every_3_days', 'Every 3 Days'),
                    ('weekly', 'Weekly')
                ],
                default='every_2_days',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='tournament',
            name='matches_per_day',
            field=models.IntegerField(
                default=1,
                help_text='Maximum matches per day (for tournaments with multiple simultaneous matches)'
            ),
        ),
        migrations.AddField(
            model_name='tournament',
            name='auto_schedule_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Enable automatic fixture scheduling'
            ),
        ),
    ]
