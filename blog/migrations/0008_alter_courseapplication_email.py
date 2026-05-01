from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0007_alter_contactrequest_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="courseapplication",
            name="email",
            field=models.CharField(max_length=100),
        ),
    ]
