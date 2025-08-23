# backend/utils/logger.py
"""
Logging configuration for Sentinel
Author: Sparsh
"""

import logging
import logging.config
import sys
from typing import Dict, Any
import json

from ..config import get_settings


def setup_logging():
    """Setup logging configuration"""
    settings = get_settings()
    
    if settings.log_format == "json":
        logging_config = get_json_logging_config(settings.log_level)
    else:
        logging_config = get_standard_logging_config(settings.log_level)
    
    logging.config.dictConfig(logging_config)
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info("Sentinel Fraud Detection System - Logging initialized")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Log format: {settings.log_format}")


def get_standard_logging_config(log_level: str) -> Dict[str, Any]:
    """Standard logging configuration"""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'detailed',
                'filename': 'logs/sentinel.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False
            }
        }
    }


def get_json_logging_config(log_level: str) -> Dict[str, Any]:
    """JSON logging configuration"""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            }
        }
    }