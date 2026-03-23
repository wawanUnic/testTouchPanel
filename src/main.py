#!/usr/bin/env python3

import time
import subprocess
import re
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

# НАСТРОЙКИ
RELAY_PIN = 18
DEVICES = [
    ("192.168.8.3", "root"),
    ("192.168.8.4", "root"),
    ("192.168.8.5", "root")
]
LOGFILE = "results.log"
POWER_ON_TIME = 120
POWER_OFF_SEQUENCE = [2, 3, 4, 5, 6, 7, 8, 10]
off_index = 0

# GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)

# SSH

def ssh_cmd(host, username, command):
    cmd = [
        "ssh",
        "-oHostKeyAlgorithms=+ssh-rsa",
        "-oPubkeyAcceptedAlgorithms=+ssh-rsa",
        "-oStrictHostKeyChecking=no",
        "-oConnectTimeout=10",
        f"{username}@{host}",
        command
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None

def get_mac(host, username):
    res = ssh_cmd(host, username, "cat /sys/class/net/$(ls /sys/class/net | grep -v lo | head -n 1)/address")
    return res.strip() if res else "MAC_ERROR"

def get_i2c_scan(host, username):
    return ssh_cmd(host, username, "sudo /usr/sbin/i2cdetect -y 1 2>&1")

def get_system_time(host, username):
    # Запрашиваем время в формате ГГГГ-ММ-ДД ЧЧ:ММ:СС
    res = ssh_cmd(host, username, "date '+%Y-%m-%d %H:%M:%S'")
    return res.strip() if res else "TIME_ERROR"

# ПАРСИНГ

def parse_i2c_addresses(scan_output):
    if not scan_output:
        return []

    found = []
    lines = scan_output.splitlines()
    for line in lines:
        parts = line.split()
        if not parts or ":" not in parts[0]:
            continue

        try:
            row_base = int(parts[0].replace(":", ""), 16)
        except ValueError:
            continue

        for i, cell in enumerate(parts[1:]):
            if cell != "--" and (re.match(r'^[0-9a-fA-F]{2}$', cell) or cell == "UU"):
                actual_addr = row_base + i
                found.append(f"0x{actual_addr:02x}")
    return found

# ОСНОВНОЙ ЦИКЛ
cycle = 1
while True:
    print(f"\n=== ЦИКЛ {cycle} ===")

    # 1. Включаем питание
    GPIO.output(RELAY_PIN, GPIO.LOW)
    print("Питание ВКЛ")
    time.sleep(POWER_ON_TIME)

    # 2. Опрос устройств
    for host, user in DEVICES:
        print(f"Опрос {host}...", end=" ", flush=True)

        mac = get_mac(host, user)
        scan = get_i2c_scan(host, user)
        remote_time = get_system_time(host, user) # Получаем время с железки
        addresses = parse_i2c_addresses(scan)

        addr_text = ", ".join(addresses) if addresses else "NONE"
        current_off_time = POWER_OFF_SEQUENCE[off_index]

        # Добавили поле "Time" в строку вывода
        line = f"Цикл: {cycle}; Time: {remote_time}; IP: {host}; MAC: {mac}; PowerOff: {current_off_time} sec; I2C: {addr_text}"

        print("OK")
        print(line)

        with open(LOGFILE, "a") as f:
            f.write(line + "\n")

    # 3. Выключаем питание
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Питание ВЫКЛ")

    # 4. Ожидание
    time.sleep(POWER_OFF_SEQUENCE[off_index])

    # Подготовка к следующему циклу
    off_index = (off_index + 1) % len(POWER_OFF_SEQUENCE)
    cycle += 1
