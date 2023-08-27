# Generated by Django 2.2.15 on 2023-08-27 03:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search_engine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('bigrams', models.BinaryField()),
                ('trigrams', models.BinaryField()),
                ('frequency', models.BinaryField()),
                ('bigrams_freq', models.BinaryField()),
                ('trigrams_freq', models.BinaryField()),
                ('part_of_speech', models.BinaryField()),
                ('text_offense', models.BinaryField()),
                ('proc_text_reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search_engine.ProcText')),
            ],
        ),
    ]