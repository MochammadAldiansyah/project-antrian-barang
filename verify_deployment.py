#!/usr/bin/env python
"""
Pre-deployment verification script
Checks if everything is ready for Vercel deployment
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are in requirements.txt"""
    print("📦 Checking requirements.txt...")
    req_file = Path('requirements.txt')
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    with open(req_file) as f:
        content = f.read().lower()
    
    required = ['django', 'gunicorn', 'dj-database-url', 'psycopg2', 'whitenoise']
    missing = []
    
    for req in required:
        if req not in content:
            missing.append(req)
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("   Consider adding them to requirements.txt")
        return False
    
    print("All required packages found")
    return True

def check_settings():
    """Check if settings.py is configured for production"""
    print("\n⚙️  Checking Django settings...")
    
    settings_file = Path('antrianbarang/settings.py')
    if not settings_file.exists():
        print("❌ settings.py not found!")
        return False
    
    with open(settings_file) as f:
        content = f.read()
    
    checks = [
        ('os.environ.get(\'SECRET_KEY\'', 'Using environment variable for SECRET_KEY'),
        ('os.environ.get(\'DEBUG\'', 'Using environment variable for DEBUG'),
        ('dj_database_url', 'Using dj_database_url for database config'),
        ('whitenoise', 'WhiteNoise middleware configured'),
        ('STATIC_ROOT', 'STATIC_ROOT configured'),
    ]
    
    all_ok = True
    for check, desc in checks:
        if check in content:
            print(f"{desc}")
        else:
            print(f"⚠️  {desc} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_files():
    """Check if required files exist"""
    print("\n📄 Checking required files...")
    
    required_files = [
        'vercel.json',
        'Procfile',
        '.env.example',
        'manage.py',
    ]
    
    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"{file} found")
        else:
            print(f"❌ {file} NOT FOUND")
            all_ok = False
    
    return all_ok

def check_wsgi():
    """Check if WSGI is configured"""
    print("\n🔧 Checking WSGI configuration...")
    
    wsgi_file = Path('antrianbarang/wsgi.py')
    if not wsgi_file.exists():
        print("❌ wsgi.py not found!")
        return False
    
    with open(wsgi_file) as f:
        content = f.read()
    
    if 'application = get_wsgi_application()' in content:
        print("WSGI application configured")
        return True
    else:
        print("❌ WSGI application not properly configured")
        return False

def main():
    print("=" * 50)
    print("🚀 PRE-DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    results = {
        'Requirements': check_requirements(),
        'Settings': check_settings(),
        'Files': check_files(),
        'WSGI': check_wsgi(),
    }
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for check, result in results.items():
        status = "PASS" if result else "⚠️  WARN/FAIL"
        print(f"{check}: {status}")
    
    all_pass = all(results.values())
    
    if all_pass:
        print("\nProject is ready for Vercel deployment!")
        print("\nNext steps:")
        print("1. Generate SECRET_KEY: python manage.py shell")
        print("2. Setup PostgreSQL (Neon/Railway/Supabase)")
        print("3. Go to Vercel Dashboard and connect GitHub")
        print("4. Add environment variables")
        print("5. Deploy!")
        print("\nFor detailed guide, see: DEPLOYMENT_GUIDE.md")
        return 0
    else:
        print("\n⚠️  Please fix the issues above before deploying")
        return 1

if __name__ == '__main__':
    sys.exit(main())
