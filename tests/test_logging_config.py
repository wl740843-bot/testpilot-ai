"""test_logging_config.py：Day 19 日志落盘与切割测试。

覆盖：
1. setup_logger 返回双通道（控制台 + 文件），级别正确
2. 文件确实生成、内容包含日志
3. 分级过滤：文件只记 WARNING 及以上，INFO 不落盘
4. 切割：文件超 maxBytes 后滚动出备份（app.log.1）
5. backupCount 限制备份数量，最旧的被删除
6. 重复调用 setup_logger 不会越加越多 handler

原则：全部用 tmp_path 临时目录 + 独立 logger 名字，不污染项目、不影响 core 的 logger。
"""
import sys
from pathlib import Path
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

import pytest

# 把项目根目录加入模块搜索路径（必须最先执行，否则找不到 logging_config 模块）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging_config import setup_logger


def test_setup_logger_returns_two_handlers(tmp_path):
    """双通道：控制台 + 文件切割，级别正确。"""
    logger = setup_logger("test_handlers", log_file=str(tmp_path / "handlers.log"))

    types = {type(h) for h in logger.handlers}
    assert StreamHandler in types
    assert RotatingFileHandler in types

    levels = {}
    for h in logger.handlers:
        # 注意：RotatingFileHandler 是 StreamHandler 的子类，必须先判文件
        if isinstance(h, RotatingFileHandler):
            levels["file"] = h.level
        else:
            levels["console"] = h.level
    assert levels["console"] == 20  # INFO
    assert levels["file"] == 30  # WARNING

    logger.handlers.clear()


def test_file_created_and_contains_warning(tmp_path):
    """日志落盘：warning 写进文件，文件存在且内容包含。"""
    log_file = tmp_path / "app.log"
    logger = setup_logger("test_write", log_file=str(log_file))

    logger.warning("落盘测试错误")

    assert log_file.exists()
    assert "落盘测试错误" in log_file.read_text(encoding="utf-8")


def test_file_only_records_warning_and_above(tmp_path):
    """分级过滤：info 不进文件，warning 进文件。"""
    log_file = tmp_path / "app.log"
    logger = setup_logger("test_level", log_file=str(log_file))

    logger.info("这是正常流水，不应进文件")
    logger.warning("这是警告，应进文件")

    content = log_file.read_text(encoding="utf-8")
    assert "这是警告，应进文件" in content
    assert "这是正常流水，不应进文件" not in content


def test_rotating_creates_backup_when_size_exceeded(tmp_path):
    """切割：max_bytes 调小后，日志打满触发滚动，出现 app.log.1。"""
    log_file = tmp_path / "app.log"
    logger = setup_logger(
        "test_rotate",
        log_file=str(log_file),
        max_bytes=200,
        backup_count=3,
    )

    # 每条消息约 500+ 字符，远超 200 字节，连打 10 条必然触发滚动
    for i in range(10):
        logger.error("x" * 500 + str(i))

    assert log_file.exists()
    assert (tmp_path / "app.log.1").exists()


def test_rotating_respects_backup_count(tmp_path):
    """backupCount=1：最多只有 app.log.1，不会出现 app.log.2。"""
    log_file = tmp_path / "app.log"
    logger = setup_logger(
        "test_rotate_count",
        log_file=str(log_file),
        max_bytes=200,
        backup_count=1,
    )

    for i in range(10):
        logger.error("x" * 500 + str(i))

    assert (tmp_path / "app.log.1").exists()
    assert not (tmp_path / "app.log.2").exists()


def test_repeat_setup_no_duplicate_handlers(tmp_path):
    """重复调用 setup_logger 同一名字：handler 不会越加越多。"""
    log_file = tmp_path / "app.log"
    name = "test_duplicate"

    setup_logger(name, log_file=str(log_file))
    setup_logger(name, log_file=str(log_file))
    logger = setup_logger(name, log_file=str(log_file))

    assert len(logger.handlers) == 2
