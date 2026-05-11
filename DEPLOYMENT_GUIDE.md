# Panduan Deploy ke Vercel

## Checklist Pre-Deployment

### 1. Generate Secret Key
```bash
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
```
Simpan output ini, akan digunakan di env variables.

### 2. Database Setup (Pilih salah satu)

#### Opsi A: Gunakan Neon PostgreSQL (Recommended - GRATIS)
1. Buka https://console.neon.tech
2. Sign up dengan GitHub
3. Create Project
4. Copy Connection String: `postgresql://user:password@host/database`

#### Opsi B: Gunakan Railway (GRATIS tapi limited)
1. Buka https://railway.app
2. Sign up dengan GitHub
3. Create Project
4. Add PostgreSQL
5. Copy DATABASE_URL

#### Opsi C: Gunakan Supabase (GRATIS)
1. Buka https://supabase.com
2. Sign up
3. Create Project
4. Copy Connection String

### 3. Vercel Deployment Steps

1. **Buka Vercel Dashboard**
   - https://vercel.com/dashboard

2. **Add New Project**
   - Click "Add New..."
   - Pilih "Project"
   - Connect GitHub
   - Select repository "Tugas-UKK"

3. **Project Settings**
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: (biarkan kosong, sudah di vercel.json)
   - Output Directory: (kosong)
   - Install Command: pip install -r requirements.txt

4. **Environment Variables** ⚠️ PENTING
   
   Tambahkan 3 variabel:
   
   ```
   SECRET_KEY = [paste dari generate_secret_key.py]
   DEBUG = False
   DATABASE_URL = [paste dari Neon/Railway/Supabase]
   ```

5. **Deploy**
   - Click "Deploy"
   - Tunggu build selesai (5-10 menit)
   - Cek logs jika ada error

### 4. Post-Deployment

Setelah deploy berhasil:

1. **Check Status**
   - Buka domain Vercel Anda
   - Seharusnya bisa buka website

2. **Database Migration**
   - Otomatis berjalan saat build
   - Jika ada error, buka Vercel CLI:
   ```bash
   vercel env pull
   python manage.py migrate
   ```

3. **Static Files**
   - Otomatis dikumpulkan saat build
   - Jika CSS/JS tidak muncul, buka terminal Vercel dan jalankan:
   ```bash
   python manage.py collectstatic --noinput
   ```

### 5. Troubleshooting

**Build Error?**
- Cek logs di Vercel Dashboard → Deployments → [latest] → Logs
- Paling sering: DATABASE_URL tidak valid

**Website blank/error 500?**
- Buka Vercel Function Logs (dashboard → Functions)
- Atau jalankan: `vercel logs`

**Static files tidak muncul?**
- Pastikan WhiteNoise middleware sudah di settings.py
- Jalankan: `python manage.py collectstatic --noinput`

**Database error?**
- Pastikan DATABASE_URL format benar
- Test koneksi locally: `python manage.py dbshell`

### 6. Vercel CLI Setup (Optional, untuk advanced)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy dari local
vercel deploy --prod

# Pull env variables
vercel env pull

# View logs
vercel logs
```

## 🚀 Quick Summary

1. Generate SECRET_KEY
2. Setup PostgreSQL di Neon/Railway/Supabase
3. Add Project di Vercel
4. Set Environment Variables (SECRET_KEY, DEBUG=False, DATABASE_URL)
5. Deploy!
6. Test di browser

---

**Butuh bantuan?** Hubungi support atau cek logs di Vercel Dashboard!
