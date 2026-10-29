"""logging_config.py：项目日志配置模块（Day 19）。

职责：统一配置日志的双通道输出：
1. 控制台（StreamHandler）    → 记 INFO 及以上，方便日常调试
2. 文件（RotatingFileHandler）→ 记 WARNING 及以上，并按大小自动切割

切割规则：文件写满 max_bytes 后自动滚动：
    app.log → app.log.1 → app.log.2 → app.log.3（最旧的被删除）
backup_count 控制最多保留几个备份，防止日志无限膨胀。
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 默认日志文件：固定放在项目根目录（本文件所在目录），
# 不依赖"从哪个目录启动程序"，避免日志乱跑到工作目录里。
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOG_FILE = str(BASE_DIR / "app.log")
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.WARNING
DEFAULT_MAX_BYTES = 1_000_000  # 1MB：文件写满就滚一次
DEFAULT_BACKUP_COUNT = 3       # 最多保留 app.log + 3 个备份


def setup_logger(
    name: str = "testpilot",
    log_file: str = DEFAULT_LOG_FILE,
    console_level: int = DEFAULT_CONSOLE_LEVEL,
    file_level: int = DEFAULT_FILE_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """创建并返回配置好的 logger。

    参数可全部自定义，方便测试时把日志写到临时目录、把切割阈值调小。
    """
    logger = logging.getLogger(name)
    # 总闸放最松（DEBUG），具体显示哪一级由各个 handler 自己把关
    logger.setLevel(logging.DEBUG)

    # 清空旧 handler（先 close 释放文件句柄），保证重复调用是幂等的
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 通道1：控制台
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(console_level)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    # 通道2：文件 + 自动切割
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
