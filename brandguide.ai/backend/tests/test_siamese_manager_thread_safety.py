"""
Thread Safety Tests for SiameseManager Singleton

Tests verify that SiameseManager is a thread-safe singleton that can be safely
accessed from multiple concurrent threads without creating duplicate instances
or encountering race conditions.
"""

import threading

from src.typography.siamese_manager import SiameseManager


class TestSiameseManagerThreadSafety:
    """Test suite for SiameseManager singleton thread safety."""

    def test_singleton_same_instance(self):
        """Verify that multiple calls return the same instance."""
        instance1 = SiameseManager()
        instance2 = SiameseManager()

        assert instance1 is instance2, "SiameseManager should return the same instance"

    def test_concurrent_initialization_single_instance(self):
        """Verify only one instance is created under concurrent access."""
        instances = []
        barrier = threading.Barrier(10)

        def create_instance():
            barrier.wait()
            instance = SiameseManager()
            instances.append(instance)

        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_instance)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(instances) == 10
        assert all(inst is instances[0] for inst in instances), (
            "All threads must receive the identical singleton instance"
        )

    def test_eager_loading_components_available(self):
        """Verify components are eagerly loaded and available."""
        manager = SiameseManager()

        # All components should be pre-loaded
        assert manager.model is not None, "Siamese model should be loaded"
        assert manager.classifier is not None, "Classifier should be loaded"
        assert manager.renderer is not None, "Renderer should be loaded"

    def test_concurrent_component_access(self):
        """Verify components can be safely accessed from multiple threads."""
        results = []

        def access_components():
            manager = SiameseManager()
            model = manager.model
            classifier = manager.classifier
            renderer = manager.renderer
            results.append(
                (model is not None, classifier is not None, renderer is not None)
            )

        threads = [threading.Thread(target=access_components) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert all(all(r) for r in results), "All component accesses should succeed"

    def test_singleton_persists(self):
        """Verify singleton persists across multiple accesses."""
        first_id = id(SiameseManager())
        second_id = id(SiameseManager())

        assert first_id == second_id, "Singleton ID should remain constant"
