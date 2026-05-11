"""Seed data for the AntrianBarang queue system"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'antrianbarang.settings')
django.setup()

from django.contrib.auth.models import User
from antrian.models import ServiceType, Counter, Officer, QueueTicket
from django.utils import timezone
from datetime import timedelta

# Create superuser
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser('admin', 'admin@antrianbarang.com', 'admin123')
    admin_user.first_name = 'Budi'
    admin_user.last_name = 'Santoso'
    admin_user.save()
    print("Superuser 'admin' created (password: admin123)")
else:
    admin_user = User.objects.get(username='admin')
    print("ℹ️  Superuser 'admin' already exists")

# Create Service Types
services = [
    ('A', 'Paket Elektronik', 'Pengambilan paket elektronik dan gadget'),
    ('B', 'Paket Dokumen', 'Pengambilan dokumen dan surat penting'),
    ('C', 'Paket Besar', 'Pengambilan paket berukuran besar'),
    ('D', 'Paket Regular', 'Pengambilan paket regular'),
]
for code, name, desc in services:
    ServiceType.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
print("Service types created")

# Create Counters
for i in range(1, 4):
    Counter.objects.get_or_create(number=i, defaults={'name': f'Meja Layanan {i:02d}'})
print("Counters created")

# Create Officer
counter1 = Counter.objects.get(number=1)
if not Officer.objects.filter(user=admin_user).exists():
    Officer.objects.create(user=admin_user, counter=counter1, employee_id='EMP-001', phone='081234567890')
    print("Officer profile created for admin")

# Create sample tickets
svc_a = ServiceType.objects.get(code='A')
svc_b = ServiceType.objects.get(code='B')

sample_tickets = [
    ('Andi Wijaya', '081111111111', svc_a, 'waiting'),
    ('Siti Rahma', '082222222222', svc_b, 'waiting'),
    ('Lukas Pratama', '083333333333', svc_a, 'waiting'),
    ('Dori Setiawan', '084444444444', svc_b, 'waiting'),
    ('Ahmad Subarja', '085555555555', svc_a, 'done'),
]

now = timezone.now()
for i, (name, phone, svc, status) in enumerate(sample_tickets):
    t, created = QueueTicket.objects.get_or_create(
        customer_name=name,
        customer_phone=phone,
        defaults={
            'service_type': svc,
            'status': status,
            'counter': counter1 if status == 'done' else None,
        }
    )
    if created and status == 'done':
        t.called_at = now - timedelta(minutes=30)
        t.served_at = now - timedelta(minutes=25)
        t.completed_at = now - timedelta(minutes=10)
        t.save()
    if created:
        print(f"  🎫 Ticket {t.ticket_number} ({t.tracking_code}) - {name}")

print("\nSeed data complete!")
print("📌 Login: admin / admin123")
print("📌 Run: python manage.py runserver")
