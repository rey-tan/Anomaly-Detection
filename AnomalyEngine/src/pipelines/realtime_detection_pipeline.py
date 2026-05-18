from __future__ import annotations

import streamlit as st

from src.pipelines.analysis_engine import RealtimeAnalysisPipeline


def run_realtime_pipeline(config, best_params):
    try:
        pipeline = RealtimeAnalysisPipeline(config, best_params)
        result = pipeline.run()
        return result.as_response(include_model=True)
    except KeyError as e:
        st.error(f"Missing config key: {e}")
    except ValueError as e:
        st.error(f"Value error: {e}")
    except Exception as e:
        st.exception(e)

    return None


    