from django.db import migrations, models


def clear_image_urls(apps, schema_editor):
    Post = apps.get_model('base', 'Post')
    Post.objects.update(image='')


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_profile_last_active'),
    ]

    operations = [
        migrations.RunPython(clear_image_urls, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='post_images/'),
        ),
    ]
