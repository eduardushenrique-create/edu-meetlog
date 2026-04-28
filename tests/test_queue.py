import pytest
import time
import sys
from pathlib import Path
from queue import Queue, PriorityQueue
import threading

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

class TestQueueSystem:
    """T5 — Queue System Tests"""
    
    def test_priority_queue_order(self):
        """Cenário 1 — Prioridade realtime"""
        pq = PriorityQueue()
        
        pq.put((2, "low_priority"))
        pq.put((1, "high_priority"))
        pq.put((3, "batch"))
        
        first = pq.get()
        assert first[1] == "high_priority"
    
    def test_backpressure(self):
        """Cenário 2 — Backpressure"""
        q = Queue(maxsize=5)
        
        for i in range(5):
            q.put(i)
        
        full = q.full()
        assert full is True
        
        try:
            q.put(99, block=False)
            assert False, "Should have raised Full"
        except:
            pass
    
    def test_concurrent_producers(self):
        """Cenário 3 — Concorrência"""
        results = []
        q = Queue()
        
        def producer(values):
            for v in values:
                q.put(v)
                time.sleep(0.001)
        
        t1 = threading.Thread(target=producer, args=(range(10),))
        t2 = threading.Thread(target=producer, args=(range(10, 20),))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        while not q.empty():
            results.append(q.get())
        
        assert len(results) == 20


class TestQueueWorker:
    """Queue worker integration tests"""
    
    def test_get_queue_stats(self):
        """Queue stats function"""
        from queue_worker import get_queue_stats
        
        stats = get_queue_stats()
        
        assert "pending" in stats
        assert "processing" in stats
        assert "done" in stats
        assert "failed" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])