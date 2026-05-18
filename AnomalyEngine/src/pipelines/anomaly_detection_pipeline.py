from __future__ import annotations

import streamlit as st

from src.pipelines.analysis_engine import StaticAnalysisPipeline


def run_pipeline(config, best_params):
    try:
        pipeline = StaticAnalysisPipeline(config, best_params)
        result = pipeline.run()
        return result.as_response()
    except KeyError as e:
        st.error(f"Missing config key: {e}")
    except ValueError as e:
        st.error(f"Value error: {e}")
    except Exception as e:
        st.exception(e)

    return None