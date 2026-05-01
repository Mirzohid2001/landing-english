from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0006_satcourse"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contactrequest",
            name="email",
            field=models.CharField(max_length=100),
        ),
    ]
