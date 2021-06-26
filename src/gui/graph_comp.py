"""
Basic graph node component
"""
default_temp = {
    "default_router": {
        "memo_size": 50,
        "mem_type": "default_memory"
    },

    "default_memory": {
        "efficiency": 0.75,
        "frequency": 2e3,
        "raw_fidelity": 0.85,
        "coherence_time": 1.3e12
    },

    "default_detector": {
        "dark_count": 0,
        "efficiency": 0.8,
        "count_rate": 5e7,
        "resolution": 1e2
    },

    "default_QKD": {
        "encoding": "polarization",
        "stack_size": 5
    },

    "default_BSM": {
        "detector_type": "default_detector"
    },

    "default_entanglement": {
        "succ_prob": 0.9,
        "degredation": 0.99
    }
}

class GraphNode:
    def __init__(self, node_name, node_type, template):  
        self.name = node_name
        self.type = node_type
        self.template = template