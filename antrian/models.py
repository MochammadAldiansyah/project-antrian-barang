from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


class ServiceType(models.Model):
    """Jenis layanan pengambilan barang"""
    name = models.CharField(max_length=100, verbose_name="Nama Layanan")
    code = models.CharField(max_length=5, unique=True, verbose_name="Kode Layanan")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jenis Layanan"
        verbose_name_plural = "Jenis Layanan"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Counter(models.Model):
    """Loket/meja layanan"""
    name = models.CharField(max_length=50, verbose_name="Nama Loket")
    number = models.IntegerField(unique=True, verbose_name="Nomor Loket")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Loket"
        verbose_name_plural = "Loket"
        ordering = ['number']

    def __str__(self):
        return f"Loket {self.number:02d}"


class Officer(models.Model):
    """Petugas loket"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer_profile')
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Loket")
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="ID Petugas")
    phone = models.CharField(max_length=20, blank=True, verbose_name="No. HP")

    class Meta:
        verbose_name = "Petugas"
        verbose_name_plural = "Petugas"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.counter}"


class QueueTicket(models.Model):
    """Tiket antrian"""
    STATUS_CHOICES = [
        ('waiting', 'Menunggu'),
        ('called', 'Dipanggil'),
        ('serving', 'Sedang Dilayani'),
        ('done', 'Selesai'),
        ('skipped', 'Dilewati'),
        ('cancelled', 'Dibatalkan'),
    ]

    ticket_number = models.CharField(max_length=10, verbose_name="Nomor Antrian")
    tracking_code = models.CharField(max_length=10, unique=True, verbose_name="Kode Tracking")
    customer_name = models.CharField(max_length=100, verbose_name="Nama Pelanggan")
    customer_phone = models.CharField(max_length=20, verbose_name="Nomor HP")
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, verbose_name="Jenis Layanan")
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Loket")
    officer = models.ForeignKey(Officer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Petugas")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='waiting', verbose_name="Status")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Daftar")
    called_at = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Dipanggil")
    served_at = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Dilayani")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Selesai")

    class Meta:
        verbose_name = "Tiket Antrian"
        verbose_name_plural = "Tiket Antrian"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self._generate_tracking_code()
        if not self.ticket_number:
            self.ticket_number = self._generate_ticket_number()
        super().save(*args, **kwargs)

    def _generate_tracking_code(self):
        """Generate unique tracking code like AB-9921"""
        while True:
            prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
            number = random.randint(1000, 9999)
            code = f"{prefix}-{number}"
            if not QueueTicket.objects.filter(tracking_code=code).exists():
                return code

    def _generate_ticket_number(self):
        """Generate sequential ticket number like A-130"""
        today = timezone.now().date()
        prefix = self.service_type.code if self.service_type else 'A'
        last_ticket = QueueTicket.objects.filter(
            created_at__date=today,
            ticket_number__startswith=prefix
        ).order_by('-created_at').first()

        if last_ticket:
            try:
                last_num = int(last_ticket.ticket_number.split('-')[1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:03d}"

    @property
    def wait_time_minutes(self):
        """Calculate wait time in minutes"""
        if self.served_at and self.created_at:
            delta = self.served_at - self.created_at
            return int(delta.total_seconds() / 60)
        elif self.status == 'waiting':
            delta = timezone.now() - self.created_at
            return int(delta.total_seconds() / 60)
        return 0

    @property
    def service_duration_minutes(self):
        """Calculate service duration in minutes"""
        if self.completed_at and self.served_at:
            delta = self.completed_at - self.served_at
            return int(delta.total_seconds() / 60)
        return 0


class DummyResi(models.Model):
    """Simulasi database paket/resi masuk dari kurir (untuk demo UKK)"""
    resi_number = models.CharField(max_length=20, unique=True, verbose_name="Nomor Resi")
    customer_name = models.CharField(max_length=100, verbose_name="Nama Pelanggan")
    customer_phone = models.CharField(max_length=20, verbose_name="No HP")
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, verbose_name="Jenis Layanan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Masuk")

    class Meta:
        verbose_name = "Resi Paket"
        verbose_name_plural = "Resi Paket"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.resi_number} - {self.customer_name}"

    @property
    def qr_string(self):
        """Format string untuk QR Code: RESI|Nama|Phone|ServiceCode"""
        return f"{self.resi_number}|{self.customer_name}|{self.customer_phone}|{self.service_type.code}"
