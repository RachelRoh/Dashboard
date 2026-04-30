#!/bin/bash

BACKUP_DIR="/home/youjeong/db_backups"
DB_PATH="/home/youjeong/Dashboard/db/dut.db"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
cp $DB_PATH $BACKUP_DIR/db_$DATE.db
find $BACKUP_DIR -name "*.db" -mtime +30 -delete