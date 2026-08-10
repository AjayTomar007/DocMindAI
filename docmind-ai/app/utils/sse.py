def format_sse(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    data_lines = "\n".join(f"data: {line}" for line in data.split("\n"))
    return f"{prefix}{data_lines}\n\n"
