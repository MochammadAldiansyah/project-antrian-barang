from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from datetime import timedelta
from .models import QueueTicket, ServiceType, Counter, Officer, DummyResi
from .forms import TakeQueueForm, CheckStatusForm


# ========================
# PUBLIC PAGES
# ========================

def ambil_antrian(request):
    """Halaman Ambil Antrian - formulir untuk mengambil nomor antrian"""
    if request.method == 'POST':
        form = TakeQueueForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            return redirect('antrian:ticket_success', tracking_code=ticket.tracking_code)
    else:
        # Auto-select service from QR code scan
        initial = {}
        service_code = request.GET.get('service', '')
        if service_code:
            try:
                svc = ServiceType.objects.get(code=service_code.upper(), is_active=True)
                initial['service_type'] = svc.pk
            except ServiceType.DoesNotExist:
                pass
        form = TakeQueueForm(initial=initial)

    today = timezone.now().date()
    today_tickets = QueueTicket.objects.filter(created_at__date=today)
    est_wait = today_tickets.filter(status='waiting').count() * 5

    context = {
        'form': form,
        'est_wait_minutes': est_wait,
        'active_page': 'ambil',
        'qr_service': request.GET.get('service', ''),
    }
    return render(request, 'antrian/ambil_antrian.html', context)


def ticket_success(request, tracking_code):
    """Halaman sukses setelah mengambil antrian"""
    ticket = get_object_or_404(QueueTicket, tracking_code=tracking_code)
    # Hitung posisi antrian
    position = QueueTicket.objects.filter(
        created_at__date=ticket.created_at.date(),
        status='waiting',
        created_at__lt=ticket.created_at
    ).count() + 1 if ticket.status == 'waiting' else 0

    context = {
        'ticket': ticket,
        'position': position,
        'active_page': 'ambil',
    }
    return render(request, 'antrian/ticket_success.html', context)


def cek_status(request):
    """Halaman Cek Status Antrian - menampilkan semua antrian hari ini + search"""
    today = timezone.now().date()
    query = request.GET.get('query', '').strip()
    results = None

    if query:
        results = QueueTicket.objects.filter(
            Q(tracking_code__icontains=query) |
            Q(customer_phone__icontains=query) |
            Q(ticket_number__icontains=query) |
            Q(customer_name__icontains=query)
        ).select_related('service_type', 'counter').order_by('-created_at')[:20]

    # Semua antrian hari ini (ditampilkan tanpa perlu search)
    today_queue = QueueTicket.objects.filter(
        created_at__date=today
    ).select_related('service_type', 'counter').order_by('created_at')

    # Antrian yang sedang dipanggil
    current_called = QueueTicket.objects.filter(
        created_at__date=today,
        status__in=['called', 'serving']
    ).select_related('counter').order_by('-called_at').first()

    # Aktivitas terakhir
    recent_activities = QueueTicket.objects.filter(
        created_at__date=today
    ).exclude(status='waiting').order_by('-called_at', '-completed_at')[:8]

    # Stats
    total_today = today_queue.count()
    waiting_count = today_queue.filter(status='waiting').count()
    done_count = today_queue.filter(status='done').count()
    next_waiting = today_queue.filter(status='waiting')[:15]

    context = {
        'query': query,
        'results': results,
        'today_queue': today_queue,
        'next_waiting': next_waiting,
        'current_called': current_called,
        'recent_activities': recent_activities,
        'total_today': total_today,
        'waiting_count': waiting_count,
        'done_count': done_count,
        'active_page': 'cek_status',
    }
    return render(request, 'antrian/cek_status.html', context)


def bantuan(request):
    """Halaman Bantuan / FAQ"""
    return render(request, 'antrian/bantuan.html', {'active_page': 'bantuan'})


@login_required
def admin_generate_resi(request):
    """Halaman Database Resi/Paket Masuk (Simulasi untuk Demo UKK)"""
    if request.method == 'POST':
        resi_number = request.POST.get('resi_number', '').strip()
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        service_type_id = request.POST.get('service_type', '')

        if resi_number and customer_name and service_type_id:
            svc = get_object_or_404(ServiceType, pk=service_type_id)
            if DummyResi.objects.filter(resi_number=resi_number).exists():
                messages.error(request, f'Nomor resi "{resi_number}" sudah ada di database.')
            else:
                DummyResi.objects.create(
                    resi_number=resi_number,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    service_type=svc
                )
                messages.success(request, f'Resi "{resi_number}" atas nama {customer_name} berhasil disimpan.')
        else:
            messages.error(request, 'Semua field wajib diisi.')
        return redirect('antrian:admin_generate_resi')

    services = ServiceType.objects.filter(is_active=True)
    all_resi = DummyResi.objects.select_related('service_type').all()
    ctx = _get_admin_context(request)
    ctx.update({
        'services': services,
        'all_resi': all_resi,
        'total_resi': all_resi.count(),
        'active_page': 'generate_resi'
    })
    return render(request, 'antrian/generate_resi.html', ctx)


@login_required
def delete_resi(request, resi_id):
    """Hapus satu resi dari database"""
    resi = get_object_or_404(DummyResi, pk=resi_id)
    resi_number = resi.resi_number
    resi.delete()
    messages.success(request, f'Resi "{resi_number}" berhasil dihapus.')
    return redirect('antrian:admin_generate_resi')


def display_antrian(request):
    """Halaman Beranda Display - menampilkan nomor antrian aktif secara besar"""
    today = timezone.now().date()
    
    current_serving = QueueTicket.objects.filter(
        created_at__date=today,
        status__in=['called', 'serving']
    ).select_related('counter', 'service_type').order_by('-called_at').first()

    upcoming = QueueTicket.objects.filter(
        created_at__date=today,
        status='waiting'
    ).select_related('service_type').order_by('created_at')[:6]

    total_waiting = QueueTicket.objects.filter(created_at__date=today, status='waiting').count()
    total_served = QueueTicket.objects.filter(created_at__date=today, status='done').count()
    est_wait = total_waiting * 5

    context = {
        'current_serving': current_serving,
        'upcoming': upcoming,
        'total_waiting': total_waiting,
        'total_served': total_served,
        'est_wait': est_wait,
        'active_page': 'display',
    }
    return render(request, 'antrian/display_antrian.html', context)


# ========================
# AUTH
# ========================

def admin_login_view(request):
    if request.user.is_authenticated:
        return redirect('antrian:admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('antrian:admin_dashboard')
        else:
            messages.error(request, 'Username atau password salah.')
    return render(request, 'antrian/admin_login.html')


def admin_logout_view(request):
    logout(request)
    return redirect('antrian:ambil_antrian')


# ========================
# ADMIN PAGES
# ========================

def _get_admin_context(request):
    """Shared context for all admin pages"""
    officer = None
    try:
        officer = request.user.officer_profile
    except (Officer.DoesNotExist, AttributeError):
        pass
    return {
        'officer': officer,
        'counters': Counter.objects.filter(is_active=True),
    }


@login_required
def admin_dashboard(request):
    """Dashboard Admin - ringkasan hari ini"""
    today = timezone.now().date()
    today_tickets = QueueTicket.objects.filter(created_at__date=today)

    total_antrian = today_tickets.count()
    antrian_selesai = today_tickets.filter(status='done').count()
    antrian_waiting = today_tickets.filter(status='waiting').count()

    # Rata-rata waktu layanan
    completed = today_tickets.filter(status='done', served_at__isnull=False, completed_at__isnull=False)
    if completed.exists():
        total_duration = sum([(t.completed_at - t.served_at).total_seconds() for t in completed])
        avg_service_time = total_duration / completed.count() / 60
    else:
        avg_service_time = 0

    current_serving = today_tickets.filter(
        status__in=['called', 'serving']
    ).select_related('counter', 'service_type', 'officer').order_by('-called_at').first()

    all_tickets = today_tickets.select_related('service_type', 'counter').order_by('-created_at')

    ctx = _get_admin_context(request)
    ctx.update({
        'total_antrian': total_antrian,
        'antrian_selesai': antrian_selesai,
        'antrian_waiting': antrian_waiting,
        'avg_service_time': round(avg_service_time, 1),
        'current_serving': current_serving,
        'all_tickets': all_tickets,
        'printer_paper_pct': 15,
        'today': timezone.now(),
        'active_page': 'dashboard',
    })
    return render(request, 'antrian/admin_dashboard.html', ctx)


@login_required
def admin_antrian_aktif(request):
    """Antrian Aktif - hanya antrian yang sedang menunggu & dipanggil"""
    today = timezone.now().date()

    current_serving = QueueTicket.objects.filter(
        created_at__date=today,
        status__in=['called', 'serving']
    ).select_related('counter', 'service_type').order_by('-called_at').first()

    waiting_tickets = QueueTicket.objects.filter(
        created_at__date=today,
        status='waiting'
    ).select_related('service_type').order_by('created_at')

    ctx = _get_admin_context(request)
    ctx.update({
        'current_serving': current_serving,
        'waiting_tickets': waiting_tickets,
        'today': timezone.now(),
        'active_page': 'antrian_aktif',
    })
    return render(request, 'antrian/admin_antrian_aktif.html', ctx)


@login_required
def admin_riwayat(request):
    """Riwayat - semua antrian yang sudah selesai/batal"""
    today = timezone.now().date()
    filter_date = request.GET.get('date', '')
    filter_status = request.GET.get('status', '')

    tickets = QueueTicket.objects.select_related('service_type', 'counter', 'officer')

    if filter_date:
        try:
            from datetime import datetime
            d = datetime.strptime(filter_date, '%Y-%m-%d').date()
            tickets = tickets.filter(created_at__date=d)
        except ValueError:
            tickets = tickets.filter(created_at__date=today)
    else:
        tickets = tickets.filter(created_at__date=today)

    if filter_status:
        tickets = tickets.filter(status=filter_status)

    tickets = tickets.order_by('-created_at')

    # Stats
    total = tickets.count()
    done = tickets.filter(status='done').count()
    skipped = tickets.filter(status='skipped').count()
    cancelled = tickets.filter(status='cancelled').count()

    ctx = _get_admin_context(request)
    ctx.update({
        'tickets': tickets,
        'filter_date': filter_date or today.strftime('%Y-%m-%d'),
        'filter_status': filter_status,
        'total': total,
        'done': done,
        'skipped': skipped,
        'cancelled': cancelled,
        'today': timezone.now(),
        'active_page': 'riwayat',
    })
    return render(request, 'antrian/admin_riwayat.html', ctx)


@login_required
def admin_pengaturan(request):
    """Pengaturan - kelola loket, layanan, dan profil"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_service':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            desc = request.POST.get('description', '').strip()
            if name and code:
                ServiceType.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
                messages.success(request, f'Layanan "{name}" berhasil ditambahkan.')

        elif action == 'toggle_service':
            svc_id = request.POST.get('service_id')
            svc = get_object_or_404(ServiceType, id=svc_id)
            svc.is_active = not svc.is_active
            svc.save()
            messages.success(request, f'Layanan "{svc.name}" {"diaktifkan" if svc.is_active else "dinonaktifkan"}.')

        elif action == 'add_counter':
            name = request.POST.get('name', '').strip()
            number = request.POST.get('number', '').strip()
            if name and number:
                Counter.objects.get_or_create(number=int(number), defaults={'name': name})
                messages.success(request, f'Loket "{name}" berhasil ditambahkan.')

        elif action == 'toggle_counter':
            c_id = request.POST.get('counter_id')
            c = get_object_or_404(Counter, id=c_id)
            c.is_active = not c.is_active
            c.save()
            messages.success(request, f'Loket "{c.name}" {"diaktifkan" if c.is_active else "dinonaktifkan"}.')

        elif action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            messages.success(request, 'Profil berhasil diperbarui.')

        return redirect('antrian:admin_pengaturan')

    services = ServiceType.objects.all().order_by('code')
    counters_all = Counter.objects.all().order_by('number')

    ctx = _get_admin_context(request)
    ctx.update({
        'services': services,
        'counters_all': counters_all,
        'today': timezone.now(),
        'active_page': 'pengaturan',
    })
    return render(request, 'antrian/admin_pengaturan.html', ctx)


# ========================
# API ENDPOINTS
# ========================

@login_required
def call_next(request):
    """Panggil antrian berikutnya"""
    if request.method == 'POST':
        today = timezone.now().date()

        # Validasi: pastikan petugas punya profil & loket aktif
        officer = None
        try:
            officer = request.user.officer_profile
        except (Officer.DoesNotExist, AttributeError):
            pass

        if not officer:
            # AUTO-CREATE UNTUK KEMUDAHAN DEMO/UKK DI DEPLOYMENT
            from .models import Counter, Officer
            default_counter, created = Counter.objects.get_or_create(
                number=1, 
                defaults={'name': 'Loket 01', 'is_active': True}
            )
            # Pastikan loket aktif
            if not default_counter.is_active:
                default_counter.is_active = True
                default_counter.save()
                
            officer = Officer.objects.create(
                user=request.user,
                counter=default_counter,
                employee_id=f"EMP-{request.user.id}"
            )
            messages.info(request, 'Profil Petugas otomatis dibuat dan di-assign ke Loket 01.')

        if not officer.counter:
            # Jika punya profil tapi belum ada loket, auto-assign
            from .models import Counter
            default_counter, created = Counter.objects.get_or_create(
                number=1, 
                defaults={'name': 'Loket 01', 'is_active': True}
            )
            officer.counter = default_counter
            officer.save()
            messages.info(request, 'Loket otomatis di-assign ke Loket 01.')

        if not officer.counter.is_active:
            messages.error(request, f'Loket {officer.counter} sedang tidak aktif. Silakan aktifkan loket terlebih dahulu di pengaturan.')
            referer = request.META.get('HTTP_REFERER', '')
            if 'antrian-aktif' in referer:
                return redirect('antrian:admin_antrian_aktif')
            return redirect('antrian:admin_dashboard')

        # Selesaikan antrian yang sedang dilayani oleh petugas ini
        QueueTicket.objects.filter(
            created_at__date=today,
            status__in=['called', 'serving'],
            counter=officer.counter,
        ).update(status='done', completed_at=timezone.now())

        # Panggil antrian berikutnya
        next_ticket = QueueTicket.objects.filter(
            created_at__date=today,
            status='waiting'
        ).order_by('created_at').first()

        if next_ticket:
            next_ticket.status = 'called'
            next_ticket.called_at = timezone.now()
            next_ticket.counter = officer.counter
            next_ticket.officer = officer
            next_ticket.save()
            messages.success(request, f'Antrian {next_ticket.ticket_number} dipanggil ke {officer.counter}!')
        else:
            messages.info(request, 'Tidak ada antrian menunggu.')

        # Redirect back to referring page or dashboard
        referer = request.META.get('HTTP_REFERER', '')
        if 'antrian-aktif' in referer:
            return redirect('antrian:admin_antrian_aktif')
        return redirect('antrian:admin_dashboard')

    return redirect('antrian:admin_dashboard')


@login_required
def update_ticket_status(request, ticket_id):
    """Update status tiket"""
    if request.method == 'POST':
        ticket = get_object_or_404(QueueTicket, id=ticket_id)
        new_status = request.POST.get('status')

        if new_status in ['serving', 'done', 'skipped', 'cancelled']:
            ticket.status = new_status
            if new_status == 'serving':
                ticket.served_at = timezone.now()
            elif new_status in ['done', 'skipped', 'cancelled']:
                ticket.completed_at = timezone.now()
                if not ticket.served_at:
                    ticket.served_at = timezone.now()
            ticket.save()
            messages.success(request, f'Status {ticket.ticket_number} diubah ke {ticket.get_status_display()}.')

        referer = request.META.get('HTTP_REFERER', '')
        if 'antrian-aktif' in referer:
            return redirect('antrian:admin_antrian_aktif')
        return redirect('antrian:admin_dashboard')

    return redirect('antrian:admin_dashboard')


def api_queue_status(request):
    """API: Real-time queue status for display & cek status pages"""
    today = timezone.now().date()

    current_serving = QueueTicket.objects.filter(
        created_at__date=today,
        status__in=['called', 'serving']
    ).select_related('counter').order_by('-called_at').first()

    upcoming = QueueTicket.objects.filter(
        created_at__date=today,
        status='waiting'
    ).order_by('created_at')[:6]

    total_waiting = QueueTicket.objects.filter(created_at__date=today, status='waiting').count()

    # All today tickets for live table
    all_tickets = QueueTicket.objects.filter(
        created_at__date=today
    ).select_related('service_type', 'counter').order_by('created_at')

    data = {
        'current': {
            'number': current_serving.ticket_number,
            'name': current_serving.customer_name,
            'counter': str(current_serving.counter) if current_serving.counter else '-',
            'status': current_serving.get_status_display(),
            'tracking_code': current_serving.tracking_code,
        } if current_serving else None,
        'upcoming': [{'number': t.ticket_number, 'tracking': t.tracking_code} for t in upcoming],
        'total_waiting': total_waiting,
        'all_tickets': [
            {
                'number': t.ticket_number,
                'tracking': t.tracking_code,
                'name': t.customer_name,
                'service': str(t.service_type),
                'status': t.status,
                'status_display': t.get_status_display(),
                'counter': str(t.counter) if t.counter else '-',
                'time': t.created_at.strftime('%H:%I'),
            }
            for t in all_tickets
        ],
    }
    return JsonResponse(data)


def api_check_ticket(request, tracking_code):
    """API: Check specific ticket status (for user notification polling)"""
    ticket = get_object_or_404(QueueTicket, tracking_code=tracking_code)
    position = 0
    if ticket.status == 'waiting':
        position = QueueTicket.objects.filter(
            created_at__date=ticket.created_at.date(),
            status='waiting',
            created_at__lt=ticket.created_at
        ).count() + 1

    data = {
        'ticket_number': ticket.ticket_number,
        'tracking_code': ticket.tracking_code,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'counter': str(ticket.counter) if ticket.counter else '-',
        'position': position,
        'called_at': ticket.called_at.strftime('%H:%M') if ticket.called_at else None,
    }
    return JsonResponse(data)
