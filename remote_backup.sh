#!/bin/bash
export BORG_PASSPHRASE='RemoteBackup2024!'

# Ключевая защита: используем системный known_hosts, а не пользовательский
# StrictHostKeyChecking=yes — отказать если fingerprint не совпадает
# UserKnownHostsFile=/etc/backup/known_hosts — системный файл принадлежит root
export BORG_RSH='ssh -i /home/testuser/.ssh/backup_key -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/etc/backup/known_hosts'

LOG='/var/log/remote_backup.log'
echo "$(date): Starting remote backup" >> $LOG

borg create --stats --compression lz4 \
    borguser@vm-backup:/store/borg_remote::backup-$(date +%Y%m%d-%H%M%S) \
    /home/testuser/important_data >> $LOG 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): Backup SUCCESS" >> $LOG
else
    echo "$(date): Backup FAILED — possible MITM attack!" >> $LOG
fi
