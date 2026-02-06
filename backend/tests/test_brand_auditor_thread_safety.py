"""
Thread Safety Tests for IntegratedBrandAuditor

Tests verify that IntegratedBrandAuditor correctly uses singleton services
in multi-threaded contexts, simulating concurrent audit requests.
"""

import threading

from src.brand_auditor import IntegratedBrandAuditor
from src.services.ml_service import MLService


class TestIntegratedBrandAuditorThreadSafety:
    """Test suite for IntegratedBrandAuditor with singleton services."""

    def test_auditor_uses_singleton_mlservice(self):
        """Verify auditor correctly uses MLService singleton when not provided."""
        # Create auditor without explicit ml_service
        auditor1 = IntegratedBrandAuditor({}, [])
        auditor2 = IntegratedBrandAuditor({}, [])

        # Both should use the same MLService singleton
        assert auditor1.ml is auditor2.ml, (
            "Both auditors should share the same MLService instance"
        )

        # Should be the global singleton
        assert auditor1.ml is MLService()

    def test_concurrent_auditor_creation(self):
        """Simulate concurrent audit requests accessing MLService."""
        auditors = []

        def create_auditor():
            # Simulate what happens in _process_audit_job
            auditor = IntegratedBrandAuditor({}, [], ml_service=None)
            auditors.append(auditor)

        threads = [threading.Thread(target=create_auditor) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All auditors should successfully get MLService
        assert len(auditors) == 20
        assert all(a.ml is not None for a in auditors)

        # All should share the same MLService singleton
        ml_service = auditors[0].ml
        assert all(a.ml is ml_service for a in auditors)

    def test_explicit_mlservice_injection_still_works(self):
        """Verify explicit injection still works (for DI compatibility)."""
        ml_service = MLService()
        auditor = IntegratedBrandAuditor({}, [], ml_service=ml_service)

        assert auditor.ml is ml_service

    def test_concurrent_auditor_with_barrier(self):
        """Test concurrent auditor creation with synchronized start."""
        auditors = []
        barrier = threading.Barrier(15)

        def create_auditor():
            barrier.wait()  # All threads start simultaneously
            auditor = IntegratedBrandAuditor({}, [])
            auditors.append(auditor)

        threads = [threading.Thread(target=create_auditor) for _ in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should share the same MLService
        assert len(set(id(a.ml) for a in auditors)) == 1, (
            "All auditors should share exactly one MLService instance"
        )
