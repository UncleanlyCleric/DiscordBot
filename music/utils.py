def create_bar(current: int, total: int, length: int = 12):
    if not total:
        return "▱" * length

    progress = int((current / total) * length)
    return "▰" * progress + "▱" * (length - progress)