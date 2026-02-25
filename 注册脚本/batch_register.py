#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv, time, os, random, yaml, logging
import phonenumbers
import requests
from pythontextnow import Client, ConversationService

# -------------------------------------------------------
# 1️⃣ 配置读入
# -------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

log_cfg = cfg.get('logging', {})
logging.basicConfig(
    level=getattr(logging, log_cfg.get('level', 'INFO').upper()),
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_cfg.get('log_file', 'logs/registration.log'))
    ]
)

# -------------------------------------------------------
# 2️⃣ 初始化
# -------------------------------------------------------
Client.set_client_config(
    username=cfg['registration']['username'],
    sid_cookie=cfg['registration']['sid_cookie']
)

def is_valid_number(number: str) -> bool:
    """确保 E.164 且符合 phonenumbers 格式。"""
    try:
        parsed = phonenumbers.parse(number, None)
        return phonenumbers.is_valid_number(parsed)
    except Exception:
        return False

def save_result(row: dict, status: str, msg: str, account_id: str = None):
    """将结果写入 CSV，保持原始列 + 状态、描述、account_id。"""
    out_row = row.copy()
    out_row['status'] = status
    out_row['message'] = msg
    out_row['account_id'] = account_id if account_id else ''
    
    file_exists = os.path.isfile('registration_results.csv')
    
    # Define fieldnames to include account_id
    fieldnames = list(row.keys()) + ['status', 'message', 'account_id']
    # Remove duplicates just in case
    fieldnames = list(dict.fromkeys(fieldnames))

    with open('registration_results.csv', 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(out_row)

# -------------------------------------------------------
# 3️⃣ 主流程
# -------------------------------------------------------
def main():
    input_path = os.path.join(os.path.dirname(__file__), 'phone_numbers.csv')
    output_path = os.path.join(os.path.dirname(__file__), 'registration_results.csv')

    # Initial write header if file doesn't exist or to reset (optional, but let's just append or create if missing)
    # If we want to start fresh each time, we should truncate. But usually batch processes might resume.
    # The original code truncated it. Let's stick to that for 'main' entry.
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=['phone_number', 'status', 'message', 'account_id']
        )
        writer.writeheader()

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            phone = row.get('phone_number', '').strip()
            if not phone:
                 continue
                 
            if not is_valid_number(phone):
                logging.warning(f'Invalid number: {phone}')
                save_result(row, 'failed', 'invalid phone')
                continue

            try:
                # ① 使用 TextNow 注册
                conversation = ConversationService([phone])
                result = conversation.send_message(f"Hello from {phone}")

                if result:
                    # ② 针对本企需要的额外接口，例如：
                    # 进行后端存储，返回 account_id
                    account_id = register_backend(phone, result)  # 这里自行实现
                    
                    # ③ 业务后续，例如：锁定或标记
                    lock_after_registration(account_id)

                    logging.info(f'Registered: {phone}')
                    save_result(row, 'success', 'registered', str(account_id))
                else:
                    logging.error(f'Register failed: {phone}')
                    save_result(row, 'failed', 'registration error')
            except Exception as e:
                logging.exception(f'Error trying to register {phone}')
                save_result(row, 'failed', str(e))

            # Rate‑limit
            delay = random.randint(cfg['rate_limit']['min_delay'],
                                   cfg['rate_limit']['max_delay'])
            logging.debug(f'Sleeping for {delay}s')
            time.sleep(delay)

def register_backend(phone: str, message_id: str) -> int:
    """
    这里演示把注册信息写到后端数据库或日志，返回统一的 account_id
    """
    # 例如，写入数据库或 JSON 文件。
    # 简化示例直接用 phone 作为 id。
    return int(abs(hash(phone)))  # 可改为真正 DB 产生的 id

def lock_after_registration(account_id: int):
    """
    如果你需要立即把账号锁定（例如：在测试阶段不让其登录），
    这里示例把账号状态设为 locked。
    """
    # 直接调用我们自己的 API 进行锁定
    lock_url = f"{cfg['locker']['base_url']}/api/accounts/{account_id}/lock"
    headers = {'Authorization': f"Bearer {cfg['locker']['api_key']}"}
    try:
        resp = requests.post(lock_url, headers=headers, timeout=10)
        resp.raise_for_status()
        logging.info(f'Locked account {account_id}')
    except Exception as exc:
        logging.error(f'Could not lock {account_id}: {exc}')

if __name__ == "__main__":
    main()