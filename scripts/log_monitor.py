#!/usr/bin/env python3
"""
Мониторинг логов AI Engineering проекта
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import re
from collections import defaultdict, Counter


class LogMonitor:
    """Мониторинг и анализ логов"""
    
    def __init__(self, log_dir: str = "/app/logs"):
        self.log_dir = Path(log_dir)
        self.services = [
            "chat-service",
            "qr-validation-service", 
            "techexpert-connector",
            "rag-service",
            "ollama-service",
            "outgoing-control-service"
        ]
        
    def get_log_files(self, service: str) -> List[Path]:
        """Получить файлы логов для сервиса"""
        log_files = []
        
        # Основной лог
        main_log = self.log_dir / f"{service}.log"
        if main_log.exists():
            log_files.append(main_log)
            
        # Лог ошибок
        error_log = self.log_dir / f"{service}_errors.log"
        if error_log.exists():
            log_files.append(error_log)
            
        # Ротированные логи
        for i in range(1, 10):  # Проверяем до 9 ротированных файлов
            rotated_log = self.log_dir / f"{service}.log.{i}"
            if rotated_log.exists():
                log_files.append(rotated_log)
                
        return log_files
    
    def parse_log_entry(self, line: str) -> Dict[str, Any]:
        """Парсинг записи лога"""
        try:
            # Пытаемся парсить как JSON (структурированные логи)
            if line.strip().startswith('{'):
                return json.loads(line.strip())
        except json.JSONDecodeError:
            pass
            
        # Парсинг обычных логов
        # Формат: 2024-01-01 12:00:00 - service - INFO - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (\w+) - (.+)'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp_str, service, level, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            return {
                "timestamp": timestamp.isoformat(),
                "service": service,
                "level": level,
                "message": message,
                "raw": line.strip()
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "service": "unknown",
            "level": "INFO",
            "message": line.strip(),
            "raw": line.strip()
        }
    
    def analyze_logs(self, service: str, hours: int = 24) -> Dict[str, Any]:
        """Анализ логов сервиса за последние N часов"""
        log_files = self.get_log_files(service)
        if not log_files:
            return {"error": f"Логи для сервиса {service} не найдены"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        entries = []
        
        # Читаем все файлы логов
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = self.parse_log_entry(line)
                        if 'timestamp' in entry:
                            try:
                                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                                if entry_time >= cutoff_time:
                                    entries.append(entry)
                            except:
                                # Если не можем парсить время, добавляем запись
                                entries.append(entry)
            except Exception as e:
                print(f"Ошибка чтения файла {log_file}: {e}")
        
        # Анализ
        analysis = {
            "service": service,
            "period_hours": hours,
            "total_entries": len(entries),
            "levels": Counter(entry.get('level', 'UNKNOWN') for entry in entries),
            "errors": [],
            "warnings": [],
            "performance_metrics": [],
            "business_events": [],
            "recent_activity": []
        }
        
        # Анализируем записи
        for entry in entries:
            level = entry.get('level', '').upper()
            message = entry.get('message', '')
            
            # Ошибки
            if level == 'ERROR':
                analysis['errors'].append({
                    "timestamp": entry.get('timestamp'),
                    "message": message,
                    "raw": entry.get('raw', '')
                })
            
            # Предупреждения
            elif level == 'WARNING':
                analysis['warnings'].append({
                    "timestamp": entry.get('timestamp'),
                    "message": message
                })
            
            # Метрики производительности
            if 'duration' in entry or 'за' in message and 's' in message:
                analysis['performance_metrics'].append(entry)
            
            # Бизнес-события
            if 'Бизнес-событие' in message or 'event' in entry:
                analysis['business_events'].append(entry)
        
        # Последняя активность (последние 10 записей)
        analysis['recent_activity'] = entries[-10:] if entries else []
        
        return analysis
    
    def get_service_status(self) -> Dict[str, Any]:
        """Получить статус всех сервисов"""
        status = {}
        
        for service in self.services:
            log_files = self.get_log_files(service)
            if not log_files:
                status[service] = {"status": "no_logs", "message": "Логи не найдены"}
                continue
            
            # Проверяем последнюю активность
            latest_activity = None
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            entry = self.parse_log_entry(last_line)
                            if 'timestamp' in entry:
                                try:
                                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                                    if latest_activity is None or entry_time > latest_activity:
                                        latest_activity = entry_time
                                except:
                                    pass
                except:
                    continue
            
            if latest_activity:
                time_diff = datetime.now() - latest_activity
                if time_diff < timedelta(minutes=5):
                    status[service] = {"status": "active", "last_activity": latest_activity.isoformat()}
                elif time_diff < timedelta(hours=1):
                    status[service] = {"status": "idle", "last_activity": latest_activity.isoformat()}
                else:
                    status[service] = {"status": "inactive", "last_activity": latest_activity.isoformat()}
            else:
                status[service] = {"status": "no_activity", "message": "Нет активности"}
        
        return status
    
    def generate_report(self, hours: int = 24) -> str:
        """Генерация отчета по логам"""
        report = []
        report.append("=" * 80)
        report.append(f"ОТЧЕТ ПО ЛОГАМ AI ENGINEERING ПРОЕКТА")
        report.append(f"Период: последние {hours} часов")
        report.append(f"Время генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Статус сервисов
        report.append("📊 СТАТУС СЕРВИСОВ:")
        status = self.get_service_status()
        for service, service_status in status.items():
            status_emoji = {
                "active": "🟢",
                "idle": "🟡", 
                "inactive": "🔴",
                "no_logs": "⚪",
                "no_activity": "⚫"
            }.get(service_status["status"], "❓")
            
            report.append(f"  {status_emoji} {service}: {service_status['status']}")
            if 'last_activity' in service_status:
                report.append(f"    Последняя активность: {service_status['last_activity']}")
        report.append("")
        
        # Детальный анализ для каждого сервиса
        for service in self.services:
            analysis = self.analyze_logs(service, hours)
            if "error" in analysis:
                continue
                
            report.append(f"🔍 АНАЛИЗ СЕРВИСА: {service.upper()}")
            report.append(f"  Всего записей: {analysis['total_entries']}")
            
            # Уровни логирования
            if analysis['levels']:
                report.append("  Уровни логирования:")
                for level, count in analysis['levels'].most_common():
                    report.append(f"    {level}: {count}")
            
            # Ошибки
            if analysis['errors']:
                report.append(f"  ❌ Ошибки ({len(analysis['errors'])}):")
                for error in analysis['errors'][-5:]:  # Последние 5 ошибок
                    report.append(f"    {error['timestamp']}: {error['message'][:100]}...")
            
            # Предупреждения
            if analysis['warnings']:
                report.append(f"  ⚠️ Предупреждения ({len(analysis['warnings'])}):")
                for warning in analysis['warnings'][-3:]:  # Последние 3 предупреждения
                    report.append(f"    {warning['timestamp']}: {warning['message'][:100]}...")
            
            # Метрики производительности
            if analysis['performance_metrics']:
                report.append(f"  ⚡ Метрики производительности: {len(analysis['performance_metrics'])} записей")
            
            # Бизнес-события
            if analysis['business_events']:
                report.append(f"  📊 Бизнес-события: {len(analysis['business_events'])} записей")
            
            report.append("")
        
        return "\n".join(report)
    
    def watch_logs(self, service: str, follow: bool = True):
        """Мониторинг логов в реальном времени"""
        log_files = self.get_log_files(service)
        if not log_files:
            print(f"Логи для сервиса {service} не найдены")
            return
        
        print(f"Мониторинг логов сервиса {service}...")
        print("Нажмите Ctrl+C для выхода")
        print("-" * 80)
        
        try:
            while follow:
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(0, 2)  # Переходим в конец файла
                            while True:
                                line = f.readline()
                                if line:
                                    entry = self.parse_log_entry(line)
                                    timestamp = entry.get('timestamp', '')
                                    level = entry.get('level', 'INFO')
                                    message = entry.get('message', '')
                                    
                                    # Цветовое кодирование уровней
                                    colors = {
                                        'ERROR': '\033[91m',    # Красный
                                        'WARNING': '\033[93m',  # Желтый
                                        'INFO': '\033[92m',     # Зеленый
                                        'DEBUG': '\033[94m',    # Синий
                                    }
                                    reset = '\033[0m'
                                    
                                    color = colors.get(level, '')
                                    print(f"{color}[{timestamp}] {level}: {message}{reset}")
                                else:
                                    time.sleep(0.1)
                    except Exception as e:
                        print(f"Ошибка чтения файла {log_file}: {e}")
                        time.sleep(1)
        except KeyboardInterrupt:
            print("\nМониторинг остановлен")


def main():
    parser = argparse.ArgumentParser(description="Мониторинг логов AI Engineering проекта")
    parser.add_argument("--log-dir", default="/app/logs", help="Директория с логами")
    parser.add_argument("--service", help="Анализ конкретного сервиса")
    parser.add_argument("--hours", type=int, default=24, help="Период анализа в часах")
    parser.add_argument("--watch", action="store_true", help="Мониторинг в реальном времени")
    parser.add_argument("--report", action="store_true", help="Генерация отчета")
    parser.add_argument("--status", action="store_true", help="Статус сервисов")
    
    args = parser.parse_args()
    
    monitor = LogMonitor(args.log_dir)
    
    if args.watch and args.service:
        monitor.watch_logs(args.service)
    elif args.report:
        print(monitor.generate_report(args.hours))
    elif args.status:
        status = monitor.get_service_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.service:
        analysis = monitor.analyze_logs(args.service, args.hours)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print("Используйте --help для просмотра доступных опций")


if __name__ == "__main__":
    main()
