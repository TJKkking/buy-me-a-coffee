"""
助手工具 - 天气和时间管理
"""
import random
from datetime import datetime, timedelta


def get_weather(city: str = "北京") -> dict:
    """
    获取指定城市的天气信息

    Args:
        city: 城市名称，如"北京"、"上海"

    Returns:
        天气信息
    """
    # 模拟天气数据
    weather_conditions = ["晴", "多云", "阴", "小雨", "阵雨"]
    temp_base = {"北京": 15, "上海": 18, "广州": 25, "深圳": 26, "杭州": 17, "成都": 16}

    base_temp = temp_base.get(city, 20)
    current_temp = base_temp + random.randint(-3, 5)
    high_temp = base_temp + random.randint(3, 8)
    low_temp = base_temp - random.randint(2, 5)
    condition = random.choice(weather_conditions)
    humidity = random.randint(40, 80)

    return {
        "success": True,
        "city": city,
        "weather": {
            "condition": condition,
            "temperature": current_temp,
            "high": high_temp,
            "low": low_temp,
            "humidity": humidity,
            "wind": f"{random.choice(['东', '南', '西', '北'])}风 {random.randint(1, 4)} 级",
        },
        "message": f"{city}今日天气：{condition}，当前 {current_temp}°C（{low_temp}°C ~ {high_temp}°C），湿度 {humidity}%",
    }


def get_current_time() -> dict:
    """
    获取当前时间

    Returns:
        当前时间信息
    """
    now = datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    return {
        "success": True,
        "datetime": now.isoformat(),
        "date": now.strftime("%Y年%m月%d日"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": weekdays[now.weekday()],
        "message": f"现在是 {now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]} {now.strftime('%H:%M')}",
    }


# 模拟内存存储
_reminders = []
_schedules = []


def set_reminder(content: str, minutes: int = 30) -> dict:
    """
    设置提醒

    Args:
        content: 提醒内容
        minutes: 多少分钟后提醒

    Returns:
        提醒信息
    """
    remind_time = datetime.now() + timedelta(minutes=minutes)
    reminder = {
        "id": len(_reminders) + 1,
        "content": content,
        "remind_at": remind_time.isoformat(),
        "created_at": datetime.now().isoformat(),
    }
    _reminders.append(reminder)

    return {
        "success": True,
        "reminder": reminder,
        "message": f"已设置提醒：{content}，将在 {minutes} 分钟后（{remind_time.strftime('%H:%M')}）提醒您",
    }


def get_reminders() -> dict:
    """
    获取所有提醒

    Returns:
        提醒列表
    """
    return {
        "success": True,
        "reminders": _reminders,
        "message": f"您有 {len(_reminders)} 个提醒" if _reminders else "暂无提醒",
    }


def add_schedule(title: str, start_time: str, duration: int = 60, notes: str = None) -> dict:
    """
    添加日程

    Args:
        title: 日程标题
        start_time: 开始时间（格式：HH:MM 或完整日期时间）
        duration: 持续时间（分钟）
        notes: 备注

    Returns:
        日程信息
    """
    # 解析时间
    now = datetime.now()
    if ":" in start_time and len(start_time) <= 5:
        # 只有时间，使用今天的日期
        hour, minute = map(int, start_time.split(":"))
        start_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if start_dt < now:
            start_dt += timedelta(days=1)  # 如果时间已过，设为明天
    else:
        start_dt = datetime.fromisoformat(start_time)

    end_dt = start_dt + timedelta(minutes=duration)

    schedule = {
        "id": len(_schedules) + 1,
        "title": title,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "duration": duration,
        "notes": notes,
        "created_at": now.isoformat(),
    }
    _schedules.append(schedule)

    return {
        "success": True,
        "schedule": schedule,
        "message": f"已添加日程：{title}，时间 {start_dt.strftime('%m月%d日 %H:%M')} - {end_dt.strftime('%H:%M')}",
    }


def get_schedules(date: str = None) -> dict:
    """
    获取日程列表

    Args:
        date: 日期（格式：YYYY-MM-DD），不指定则返回全部

    Returns:
        日程列表
    """
    if date:
        filtered = [
            s for s in _schedules if s["start_time"].startswith(date)
        ]
    else:
        filtered = _schedules

    return {
        "success": True,
        "schedules": filtered,
        "message": f"您有 {len(filtered)} 个日程" if filtered else "暂无日程",
    }

