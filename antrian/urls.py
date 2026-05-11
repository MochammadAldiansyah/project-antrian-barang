from django.urls import path
from . import views

app_name = 'antrian'

urlpatterns = [
    # Public pages
    path('', views.ambil_antrian, name='ambil_antrian'),
    path('ambil-antrian/', views.ambil_antrian, name='ambil_antrian_alt'),
    path('ticket/<str:tracking_code>/', views.ticket_success, name='ticket_success'),
    path('cek-status/', views.cek_status, name='cek_status'),
    path('display/', views.display_antrian, name='display_antrian'),
    path('bantuan/', views.bantuan, name='bantuan'),

    # Auth
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # Admin pages
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-antrian-aktif/', views.admin_antrian_aktif, name='admin_antrian_aktif'),
    path('admin-riwayat/', views.admin_riwayat, name='admin_riwayat'),
    path('admin-pengaturan/', views.admin_pengaturan, name='admin_pengaturan'),
    path('admin-generate-resi/', views.admin_generate_resi, name='admin_generate_resi'),
    path('admin-delete-resi/<int:resi_id>/', views.delete_resi, name='delete_resi'),

    # API endpoints
    path('api/call-next/', views.call_next, name='call_next'),
    path('api/update-status/<int:ticket_id>/', views.update_ticket_status, name='update_ticket_status'),
    path('api/queue-status/', views.api_queue_status, name='api_queue_status'),
    path('api/check-ticket/<str:tracking_code>/', views.api_check_ticket, name='api_check_ticket'),
]
