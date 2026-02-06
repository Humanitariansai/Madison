"""
Thread Safety Tests for MLService Singleton

Tests verify that MLService is a thread-safe singleton that can be safely
accessed from multiple concurrent threads without creating duplicate instances
or encountering race conditions.
"""

import threading

from src.services.ml_service import MLService


class TestMLServiceThreadSafety:
    """Test suite for MLService singleton thread safety."""

    def test_singleton_same_instance(self):
        """Verify that multiple calls return the same instance."""
        instance1 = MLService()
        instance2 = MLService()

        assert instance1 is instance2, "MLService should return the same instance"

    def test_concurrent_initialization_single_instance(self):
        """Verify only one instance is created under concurrent access."""
        instances = []
        barrier = threading.Barrier(10)  # Synchronize thread start

        def create_instance():
            barrier.wait()  # All threads start at the same time
            instance = MLService()
            instances.append(instance)

        # Spawn 10 threads simultaneously
        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_instance)
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Assert: All threads got the SAME instance
        assert len(instances) == 10, "Should have 10 results"
        assert all(inst is instances[0] for inst in instances), (
            "All threads must receive the identical singleton instance"
        )

    def test_eager_loading_models_available(self):
        """Verify models are eagerly loaded and available."""
        service = MLService()

        # All models should be pre-loaded (not None)
        assert service.sift is not None, "SIFT should be loaded"
        assert service.clip_model is not None, "CLIP model should be loaded"
        assert service.clip_processor is not None, "CLIP processor should be loaded"
        assert service.nlp_pipe is not None, "NLP pipeline should be loaded"

    def test_concurrent_model_access(self):
        """Verify models can be safely accessed from multiple threads."""
        results = []

        def access_models():
            service = MLService()
            # Access all models
            sift = service.sift
            clip = service.clip_model
            nlp = service.nlp_pipe
            results.append((sift is not None, clip is not None, nlp is not None))

        threads = [threading.Thread(target=access_models) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should successfully access models
        assert len(results) == 20
        assert all(all(r) for r in results), "All model accesses should succeed"

    def test_singleton_persists(self):
        """Verify singleton persists across multiple accesses."""
        first_id = id(MLService())
        second_id = id(MLService())

        assert first_id == second_id, "Singleton ID should remain constant"
