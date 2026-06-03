from __future__ import annotations

import logging

from src.pipelines.analysis_engine import StaticAnalysisPipeline

logger = logging.getLogger(__name__)


def run_pipeline(config, best_params):
    try:
        print(f"run_pipeline: config={config}", flush=True)
        print(f"run_pipeline: best_params={best_params}", flush=True)
        pipeline = StaticAnalysisPipeline(config, best_params)
        result = pipeline.run()
        try:
            labels = result.labels
            # count anomalies per detector if available
            counts = {k: int((v == -1).sum()) if hasattr(v, "__array__") or isinstance(v, list) else 0 for k, v in labels.items()}
            print(f"Pipeline labels anomaly counts: {counts}", flush=True)
        except Exception:
            pass
        return result.as_response()
    except KeyError as e:
        logger.error("Missing config key: %s", e)
    except ValueError as e:
        logger.error("Value error: %s", e)
    except Exception:
        logger.exception("Unexpected error running pipeline")
        print("Unexpected error running pipeline. See logs for stack.", flush=True)

    return None