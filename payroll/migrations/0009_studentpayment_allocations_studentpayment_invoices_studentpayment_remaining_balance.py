from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0008_schoolfee_school_classes'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentpayment',
            name='allocations',
            field=models.JSONField(blank=True, default=list, help_text='Allocation details for each invoice covered by the payment.'),
        ),
        migrations.AddField(
            model_name='studentpayment',
            name='invoices',
            field=models.JSONField(blank=True, default=list, help_text='List of invoice IDs this payment covered.'),
        ),
        migrations.AddField(
            model_name='studentpayment',
            name='remaining_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
