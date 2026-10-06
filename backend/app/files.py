"""生成文件的滚动清理：每类产物只保留最新 N 个，防止磁盘无限增长。"""
from pathlib import Path


def prune_dir(directory, keep: int = 200) -> None:
    d = Path(directory)
    if not d.exists():
        return
    files = sorted(d.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[keep:]:
        try:
            p.unlink()
        except OSError:
            pass
