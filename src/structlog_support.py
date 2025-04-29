def configure_structlog(processors, log_format, structlog_context=None):
    import structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    if structlog_context:
        logger = structlog.get_logger()
        logger = logger.bind(**structlog_context)
        return logger
    return structlog.get_logger() 