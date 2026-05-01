from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0008_alter_courseapplication_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Asosiy sozlama", max_length=100)),
                ("bot_token", models.CharField(max_length=255)),
                (
                    "chat_ids",
                    models.TextField(
                        help_text="Har bir chat ID ni yangi qatorda yozing (masalan: -100123..., -100456...)"
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Telegram sozlamasi",
                "verbose_name_plural": "Telegram sozlamalari",
                "ordering": ["-updated_at"],
            },
        ),
    ]
