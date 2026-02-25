#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv, yaml, requests, logging
import time
import os

# -----------------------------------------
# 读取配置
# -----------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

logging.basicConfig(
    level=getattr(logging, cfg['logging'].get('level', 'INFO').upper()),
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(cfg['logging'].get('log_file', 'logs/lock.log'))
    ])

LOCK_URL_TEMPLATE = "{base_url}/api/accounts/{id}/lock"
UNLOCK_URL_TEMPLATE = "{base_url}/api/accounts/{id}/unlock"

headers = {'Authorization': f"Bearer {cfg['locker']['api_key']}"}

# -----------------------------------------
# 读取需要锁定/解锁的账号列表
# -----------------------------------------
def read_account_ids(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'account_id' in row and row['account_id']:
                yield int(row['account_id'])

# -----------------------------------------
# 批量操作
# -----------------------------------------
def batch_lock(ids, action='lock', throttle=0.5):
    """
    action: 'lock' | 'unlock'
    throttle: 秒 > 0 同一时间只请求一个
    """
    url_template = LOCK_URL_TEMPLATE if action == 'lock' else UNLOCK_URL_TEMPLATE
    for aid in ids:
        base_url = cfg['locker']['base_url'].strip().rstrip('/')
        # Remove quotes if present in config (common mistake in yaml)
        if base_url.startswith('"') and base_url.endswith('"'):
            base_url = base_url[1:-1]
            
        url = url_template.format(base_url=base_url, id=aid)
        try:
            resp = requests.post(url, headers=headers, timeout=10)
            resp.raise_for_status()
            logging.info(f'{action.capitalize()}d {aid}')
        except Exception as exc:
            logging.error(f'{action} {aid} failed: {exc}')
        time.sleep(throttle)

# -----------------------------------------
# 入口
# -----------------------------------------
if __name__ == "__main__":
    results_path = os.path.join(os.path.dirname(__file__), 'registration_results.csv')
    if os.path.exists(results_path):
        ids_to_lock = read_account_ids(results_path)
        batch_lock(ids_to_lock, action='lock', throttle=1.0)
    else:
        logging.error(f"File not found: {results_path}")