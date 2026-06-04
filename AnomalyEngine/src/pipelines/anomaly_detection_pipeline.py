from __future__ import annotations

import logging

from src.pipelines.analysis_engine import StaticAnalysisPipeline

logger = logging.getLogger(__name__)


def run_pipeline(config, best_params):
    try:
        pipeline = StaticAnalysisPipeline(config, best_params)
        result = pipeline.run()
        return result.as_response()
    except KeyError as e:
        logger.error("Missing config key: %s", e)
    except ValueError as e:
        logger.error("Value error: %s", e)
    except Exception:
        logger.exception("Unexpected error running pipeline")
    return None