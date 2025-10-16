from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('appLiher', '0001_initial'),  
    ]

    operations = [
        migrations.AddField(
            model_name='inventario',
            name='catalogo',
            field=models.ForeignKey(
                to='appLiher.Catalogo', 
                on_delete=django.db.models.deletion.CASCADE,
                null=True,   # temporalmente permitir nulos si ya hay datos
                blank=True
            ),
        ),
    ]
