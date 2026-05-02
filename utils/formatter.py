import re


_ESCAPE_RE = re.compile(r'([\\_*\[\]()~`#+\-=|{}.!])')


def escape(text: str) -> str:
    """MarkdownV2에서 특수문자를 이스케이프합니다."""
    return _ESCAPE_RE.sub(r'\\\1', str(text))


def build_caption(brand: str, name: str, sizes: list[str], features: str) -> str:
    """텔레그램 채널용 MarkdownV2 캡션을 생성합니다."""
    size_str = " \\| ".join(f"`{s.strip()}`" for s in sizes if s.strip())

    lines = [
        f"✨ \\#{escape(brand)} ✨",
        "━━━━━━━━━━━━━━━━",
        "",
        f"👕 *{escape(name)}*",
        "",
        f"📏 *사이즈*",
        size_str,
        "",
        f"⭐ *특징*",
    ]

    for feature_line in features.strip().splitlines():
        if feature_line.strip():
            lines.append(f">{escape(feature_line)}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)
