from json import load
from mpi4py import MPI
from networkx import Graph, dijkstra_path
from numpy import mean

from .topology import Topology as Topo
from ..kernel.timeline import Timeline
from ..kernel.p_timeline import ParallelTimeline, AsyncParallelTimeline
from .node import BSMNode, QuantumRouter
from ..components.optical_channel import QuantumChannel, ClassicalChannel


class RouterNetTopo(Topo):
    """Class for generating quantum communication network with quantum routers

    Class RouterNetTopo is the child of class Topology. Quantum routers, BSM
    nodes, quantum  channels, classical channels and timeline for simulation
    could be generated by using this class. Different processes in the parallel
    simulation could use the same configuration file to generate network
    requrired for the parallel simulation.

    Attributes:
        bsm_to_router_map (Dict[str, List[Node]]): mapping of bsm node to two connected routers
        nodes (Dict[str, List[Node]]): mapping of type of node to a list of same type node.
        qchannels (List[QuantumChannel]): list of quantum channel objects in network.
        cchannels (List[ClassicalChannel]): list of classical channel objects in network.
        tl (Timeline): the timeline used for simulation
    """
    ALL_GROUP = "groups"
    ASYNC = "async"
    BSM_NODE = "BSMNode"
    GROUP = "group"
    IP = "ip"
    IS_PARALLEL = "is_parallel"
    LOOKAHEAD = "lookahead"
    MEET_IN_THE_MID = "meet_in_the_middle"
    MEMO_ARRAY_SIZE = "memo_size"
    PORT = "port"
    PROC_NUM = "process_num"
    QUANTUM_ROUTER = "QuantumRouter"
    SYNC = "sync"

    def __init__(self, conf_file_name: str):
        self.bsm_to_router_map = {}
        super().__init__(conf_file_name)

    def _load(self, filename):
        with open(filename, 'r') as fh:
            config = load(fh)
        # quantum connections is supported by sequential simulation so far
        if not config[self.IS_PARALLEL]:
            self._add_qconnections(config)
        self._add_timeline(config)
        self._map_bsm_routers(config)
        self._add_nodes(config)
        self._add_bsm_node_to_router()
        self._add_qchannels(config)
        self._add_cchannels(config)
        self._add_cconnections(config)
        self._generate_forwaring_table(config)

    def _add_timeline(self, config):
        stop_time = config.get(Topo.STOP_TIME, float('inf'))
        if config.get(self.IS_PARALLEL, False):
            assert MPI.COMM_WORLD.Get_size() == config[self.PROC_NUM]
            rank = MPI.COMM_WORLD.Get_rank()

            tl_type = config[self.ALL_GROUP][rank][Topo.TYPE]
            lookahead = config[self.LOOKAHEAD]
            ip = config[self.IP]
            port = config[self.PORT]
            if tl_type == self.SYNC:
                self.tl = ParallelTimeline(lookahead, qm_ip=ip, qm_port=port,
                                           stop_time=stop_time)
            elif tl_type == self.ASYNC:
                self.tl = AsyncParallelTimeline(lookahead, qm_ip=ip,
                                                qm_port=port,
                                                stop_time=stop_time)
            else:
                raise NotImplementedError("Unknown type of timeline")
        else:
            self.tl = Timeline(stop_time)

    def _map_bsm_routers(self, config):
        for qc in config[Topo.ALL_Q_CHANNEL]:
            src, dst = qc[Topo.SRC], qc[Topo.DST]
            if dst in self.bsm_to_router_map:
                self.bsm_to_router_map[dst].append(src)
            else:
                self.bsm_to_router_map[dst] = [src]

    def _add_nodes(self, config):
        rank = MPI.COMM_WORLD.Get_rank()
        size = MPI.COMM_WORLD.Get_size()

        for node in config[Topo.ALL_NODE]:
            seed, type = node[Topo.SEED], node[Topo.TYPE],
            group, name = node.get(self.GROUP, 0), node[Topo.NAME]
            assert group < size, "Group id is out of scope" \
                                 " ({} >= {}).".format(group, size)
            if group == rank:
                if type == self.BSM_NODE:
                    others = self.bsm_to_router_map[name]
                    node_obj = BSMNode(name, self.tl, others)
                elif type == self.QUANTUM_ROUTER:
                    memo_size = node.get(self.MEMO_ARRAY_SIZE, 0)
                    if memo_size:
                        node_obj = QuantumRouter(name, self.tl, memo_size)
                    else:
                        print("WARN: the size of memory on quantum router {} "
                              "is not set".format(name))
                        node_obj = QuantumRouter(name, self.tl)
                else:
                    raise NotImplementedError("Unknown type of node")

                node_obj.set_seed(seed)
                if type in self.nodes:
                    self.nodes[type].append(node_obj)
                else:
                    self.nodes[type] = [node_obj]
            else:
                self.tl.add_foreign_entity(name, group)

    def _add_bsm_node_to_router(self):
        for bsm in self.bsm_to_router_map:
            r0_str, r1_str = self.bsm_to_router_map[bsm]
            r0 = self.tl.get_entity_by_name(r0_str)
            r1 = self.tl.get_entity_by_name(r1_str)
            if r0 is not None:
                r0.add_bsm_node(bsm, r1_str)
            if r1 is not None:
                r1.add_bsm_node(bsm, r0_str)

    def _add_qconnections(self, config):
        for q_connect in config.get(Topo.ALL_QC_CONNECT, []):
            node1 = q_connect[Topo.CONNECT_NODE_1]
            node2 = q_connect[Topo.CONNECT_NODE_2]
            attenuation = q_connect[Topo.ATTENUATION]
            distance = q_connect[Topo.DISTANCE] // 2
            type = q_connect[Topo.TYPE]
            cc_delay = []
            for cc in config.get(self.ALL_C_CHANNEL, []):
                if cc[self.SRC] == node1 and cc[self.DST] == node2:
                    cc_delay.append(cc.delay)
                elif cc[self.SRC] == node2 and cc[self.DST] == node1:
                    cc_delay.append(cc.delay)

            for cc in config.get(self.ALL_CC_CONNECT, []):
                if (cc[self.CONNECT_NODE_1] == node1
                    and cc[self.CONNECT_NODE_2] == node2) \
                        or (cc[self.CONNECT_NODE_1] == node2
                            and cc[self.CONNECT_NODE_2] == node1):
                    delay = cc.get(self.DELAY,
                                   cc.get(self.DISTANCE, 1000) / 2e-4)
                    cc_delay.append(delay)
            if len(cc_delay) == 0:
                assert 0, q_connect
            cc_delay = mean(cc_delay) // 2
            if type == self.MEET_IN_THE_MID:
                bsm_name = "BSM.{}.{}.auto".format(node1, node2)
                bsm_info = {self.NAME: bsm_name,
                            self.TYPE: self.BSM_NODE,
                            self.SEED: 0}
                config[self.ALL_NODE].append(bsm_info)

                for src in [node1, node2]:
                    qc_name = "QC.{}.{}".format(src, bsm_name)
                    qc_info = {self.NAME: qc_name,
                               self.SRC: src,
                               self.DST: bsm_name,
                               self.DISTANCE: distance,
                               self.ATTENUATION: attenuation}
                    if not self.ALL_Q_CHANNEL in config:
                        config[self.ALL_Q_CHANNEL] = []
                    config[self.ALL_Q_CHANNEL].append(qc_info)

                    cc_name = "CC.{}.{}".format(src, bsm_name)
                    cc_info = {self.NAME: cc_name,
                               self.SRC: src,
                               self.DST: bsm_name,
                               self.DISTANCE: distance,
                               self.DELAY: cc_delay}
                    if not self.ALL_C_CHANNEL in config:
                        config[self.ALL_C_CHANNEL] = []
                    config[self.ALL_C_CHANNEL].append(cc_info)

                    cc_name = "CC.{}.{}".format(bsm_name, src)
                    cc_info = {self.NAME: cc_name,
                               self.SRC: bsm_name,
                               self.DST: src,
                               self.DISTANCE: distance,
                               self.DELAY: cc_delay}
                    config[self.ALL_C_CHANNEL].append(cc_info)
            else:
                raise NotImplementedError("Unknown type of quantum connection")

    def _generate_forwaring_table(self, config):
        graph = Graph()
        for node in config[Topo.ALL_NODE]:
            if node[Topo.TYPE] == self.QUANTUM_ROUTER:
                graph.add_node(node[Topo.NAME])

        costs = {}
        if config[self.IS_PARALLEL]:
            for qc in config[self.ALL_Q_CHANNEL]:
                router, bsm = qc[self.SRC], qc[self.DST]
                if not bsm in costs:
                    costs[bsm] = [router, qc[self.DISTANCE]]
                else:
                    costs[bsm] = [router] + costs[bsm]
                    costs[bsm][-1] += qc[self.DISTANCE]
        else:
            for qc in self.qchannels:
                router, bsm = qc.sender.name, qc.receiver
                if not bsm in costs:
                    costs[bsm] = [router, qc.distance]
                else:
                    costs[bsm] = [router] + costs[bsm]
                    costs[bsm][-1] += qc.distance

        graph.add_weighted_edges_from(costs.values())
        for src in self.nodes[self.QUANTUM_ROUTER]:
            for dst_name in graph.nodes:
                if src.name == dst_name:
                    continue
                if dst_name > src.name:
                    path = dijkstra_path(graph, src.name, dst_name)
                else:
                    path = dijkstra_path(graph, dst_name, src.name)[::-1]
                next_hop = path[1]
                # routing protocol locates at the bottom of the protocol stack
                routing_protocol = src.network_manager.protocol_stack[0]
                routing_protocol.add_forwarding_rule(dst_name, next_hop)
