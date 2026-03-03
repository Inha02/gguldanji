"""
의존성 관리
==========
PriceEstimator 싱글턴 인스턴스 관리
"""

from crawler.pipeline.step3c_inference import PriceEstimator

_engine: PriceEstimator | None = None


def get_engine() -> PriceEstimator:
    """PriceEstimator 싱글턴. 서버 기동 시 한 번만 초기화."""
    global _engine
    if _engine is None:
        _engine = PriceEstimator()
    return _engine