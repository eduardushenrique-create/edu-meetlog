import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from audio_capture import ChunkBuffer, SAMPLE_RATE

class TestChunking:
    """T4 — Chunking Tests"""
    
    @pytest.fixture
    def buffer(self):
        return ChunkBuffer(max_duration=3)
    
    def test_segmentation_size(self, buffer):
        """Cenário 1 — Segmentação correta"""
        chunk = np.random.randn(SAMPLE_RATE * 3)
        buffer.add(chunk)
        
        chunks = buffer.get_chunks()
        
        assert len(chunks) <= 2, f"Expected ≤2 chunks, got {len(chunks)}"
    
    def test_temporal_continuity(self, buffer):
        """Cenário 2 — Continuidade temporal"""
        np.random.seed(42)
        
        for i in range(10):
            chunk = np.random.randn(SAMPLE_RATE // 2)
            buffer.add(chunk)
        
        chunks = buffer.get_chunks()
        
        total_samples = sum(len(c) for c in chunks)
        assert total_samples <= SAMPLE_RATE * 5, "Buffer should limit to ~5s max"
    
    def test_buffer_overflow(self, buffer):
        """Cenário 3 — Buffer overflow"""
        np.random.seed(42)
        
        for i in range(100):
            chunk = np.random.randn(SAMPLE_RATE // 2)
            buffer.add(chunk)
        
        chunks = buffer.get_chunks()
        
        assert buffer.current_chunk is not None or len(buffer.buffer) <= 10

    def test_chunks_keep_capture_start_time(self, buffer):
        chunk = np.random.randn(SAMPLE_RATE * 3)
        buffer.add(chunk, chunk_start_time=123.5)

        chunks = buffer.get_chunks()

        assert chunks[0][0] == 123.5
        assert len(chunks[0][1]) == SAMPLE_RATE * 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
