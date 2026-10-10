# SPDX-License-Identifier: Apache-2.0
"""Tests for logging configuration filters."""

import logging

from omlx.logging_config import AdminStatsAccessFilter, apply_logger_levels


class TestApplyLoggerLevels:
    def test_applies_named_levels_case_insensitive(self):
        name = "omlx.engine.dflash"
        before = logging.getLogger(name).level
        try:
            applied = apply_logger_levels(f" {name}=debug , {name}=INFO")
            assert applied == [f"{name}=DEBUG", f"{name}=INFO"]
            assert logging.getLogger(name).level == logging.INFO
        finally:
            logging.getLogger(name).setLevel(before)

    def test_skips_empty_and_garbled_entries(self):
        name = "omlx.engine.dflash"
        before = logging.getLogger(name).level
        try:
            assert apply_logger_levels("") == []
            assert apply_logger_levels(",,,=DEBUG,omlx.engine.dflash=NOPE") == []
            assert logging.getLogger(name).level == before
        finally:
            logging.getLogger(name).setLevel(before)

    def test_debug_raise_lowers_restrictive_root_handlers(self):
        """A per-logger DEBUG raise must reach server.log: its file handler
        carries the server log level, so without lowering it the records
        would flow to stderr/launchd logs only and vanish from the file
        ops greps (e.g. only the 1st dflash park at INFO, parking looks
        broken)."""
        root = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        root.addHandler(handler)
        logger = logging.getLogger("omlx.logging.test.dflash")
        logger.setLevel(logging.INFO)
        try:
            apply_logger_levels("omlx.logging.test.dflash=DEBUG")
            assert handler.level == logging.DEBUG
        finally:
            root.removeHandler(handler)
            logger.setLevel(logging.NOTSET)

    def test_raise_never_lifts_nor_touches_permissive_handlers(self):
        """Only a more-verbose raise lowers handlers, and only downward: a
        quieter raise (WARNING on an INFO logger) must not make sinks
        noisier, and a DEBUG raise must not add filtering to NOTSET
        (pass-all) handlers."""
        root = logging.getLogger()
        info_handler = logging.StreamHandler()
        info_handler.setLevel(logging.INFO)
        notset_handler = logging.StreamHandler()
        notset_handler.setLevel(logging.NOTSET)
        error_handler = logging.StreamHandler()
        error_handler.setLevel(logging.ERROR)
        root.addHandler(info_handler)
        root.addHandler(notset_handler)
        root.addHandler(error_handler)
        quieter = logging.getLogger("omlx.logging.test.quieter")
        quieter.setLevel(logging.INFO)
        verbose = logging.getLogger("omlx.logging.test.verbose")
        verbose.setLevel(logging.INFO)
        try:
            apply_logger_levels("omlx.logging.test.quieter=WARNING")
            assert info_handler.level == logging.INFO
            assert error_handler.level == logging.ERROR
            apply_logger_levels("omlx.logging.test.verbose=DEBUG")
            assert notset_handler.level == logging.NOTSET
            assert error_handler.level == logging.DEBUG
        finally:
            root.removeHandler(info_handler)
            root.removeHandler(notset_handler)
            root.removeHandler(error_handler)
            quieter.setLevel(logging.NOTSET)
            verbose.setLevel(logging.NOTSET)


class TestAdminStatsAccessFilter:
    """Tests for the admin polling access log filter."""

    def setup_method(self):
        self.filter = AdminStatsAccessFilter()

    def _make_record(self, msg: str) -> logging.LogRecord:
        return logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_suppresses_admin_stats(self):
        record = self._make_record('127.0.0.1 - "GET /admin/api/stats HTTP/1.1" 200')
        assert self.filter.filter(record) is False

    def test_suppresses_admin_stats_with_params(self):
        record = self._make_record(
            '127.0.0.1 - "GET /admin/api/stats?scope=alltime HTTP/1.1" 200'
        )
        assert self.filter.filter(record) is False

    def test_suppresses_admin_login(self):
        record = self._make_record(
            '127.0.0.1 - "POST /admin/api/login HTTP/1.1" 200'
        )
        assert self.filter.filter(record) is False

    def test_allows_other_requests(self):
        record = self._make_record('127.0.0.1 - "GET /v1/models HTTP/1.1" 200')
        assert self.filter.filter(record) is True

    def test_allows_health_check(self):
        record = self._make_record('127.0.0.1 - "GET /health HTTP/1.1" 200')
        assert self.filter.filter(record) is True

    def test_allows_chat_completions(self):
        record = self._make_record(
            '127.0.0.1 - "POST /v1/chat/completions HTTP/1.1" 200'
        )
        assert self.filter.filter(record) is True
