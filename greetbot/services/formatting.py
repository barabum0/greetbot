def convert_seconds(seconds: int) -> str:
    seconds_in_minute = 60
    seconds_in_hour = 3600
    seconds_in_day = 86400

    days = seconds // seconds_in_day
    hours = (seconds % seconds_in_day) // seconds_in_hour
    minutes = (seconds % seconds_in_hour) // seconds_in_minute
    remaining_seconds = seconds % seconds_in_minute

    # Собираем строку с результатом, исключая единицы времени, которые равны нулю.
    parts = []
    if days > 0:
        parts.append(f"{days} {'день' if days == 1 else 'дней'}")
    if hours > 0:
        parts.append(f"{hours} {'час' if hours == 1 else 'часов'}")
    if minutes > 0:
        parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут'}")
    if remaining_seconds > 0 or not parts:
        parts.append(f"{remaining_seconds} {'секунда' if remaining_seconds == 1 else 'секунд'}")

    return " ".join(parts)
