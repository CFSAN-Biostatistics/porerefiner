"""Shared pytest / Hypothesis configuration.

Registers a Hypothesis profile that suppresses the ``too_slow`` /
data-generation health checks. Several strategies in this suite build peewee
model instances, which is inherently slow; under CI or a loaded machine the
default health checks trip non-deterministically and produce flaky failures
that are unrelated to the code under test. We keep example counts modest and
drop the wall-clock deadline so runs are deterministic.
"""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "porerefiner",
    deadline=None,
    suppress_health_check=(
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.filter_too_much,
    ),
)

settings.load_profile("porerefiner")
