"""Pluggable source adapters.

Every source emits the same :class:`~basr.adapters.base.RawDoc` shape, so the
pipeline is immune to any single source's API changes, rate limits, or outages.
"""

from .base import RawDoc, SourceAdapter, hash_author

__all__ = ["RawDoc", "SourceAdapter", "hash_author"]
