from numpy import random
import math
from event import Event
from timeline import Timeline
from BB84 import BB84
import topology
from process import Process

if __name__ == "__main__":
    random.seed(1)
    import sys
    frequency = sys.argv[1] # GHz
    filename = "results/sensitivity/freq_mean_bb84_"+frequency+".log"
    frequency = float(frequency)
    fh = open(filename,'w')

    for mean_num in range(1,2):
        tl = Timeline()
        qc = topology.QuantumChannel("qc", tl, distance=20000, polarization_fidelity=0.97, attenuation=0.0002)
        cc = topology.ClassicalChannel("cc", tl, distance=20000)
        cc.delay+= 10**9

        # Alice
        ls = topology.LightSource("alice.lightsource", tl, frequency=frequency*10**9, mean_photon_num=mean_num/10, direct_receiver=qc)
        components = {"lightsource": ls, "cchannel":cc, "qchannel":qc}
        alice = topology.Node("alice", tl, components=components)
        qc.set_sender(ls)
        cc.add_end(alice)
        tl.entities.append(alice)

        # Bob
        detectors = [{"efficiency":0.8, "dark_count":10, "time_resolution":10, "count_rate":50*10**6},
                     {"efficiency":0.8, "dark_count":10, "time_resolution":10, "count_rate":50*10**6}]
        splitter = {}
        qsd = topology.QSDetector("bob.qsdetector", tl, detectors=detectors, splitter=splitter)
        components = {"detector":qsd, "cchannel":cc, "qchannel":qc}
        bob = topology.Node("bob",tl,components=components)
        qc.set_receiver(qsd)
        cc.add_end(bob)
        tl.entities.append(bob)

        # BB84
        bba = BB84("bba", tl, role=0)
        bbb = BB84("bbb", tl, role=1)
        bba.assign_node(alice)
        bbb.assign_node(bob)
        bba.another = bbb
        bbb.another = bba
        alice.protocol = bba
        bob.protocol = bbb

        process = Process(bba, "generate_key", [256,math.inf,0.06*10**12])
        event = Event(0,process)
        tl.schedule(event)
        tl.run()
        fh.write(str(frequency))
        fh.write(' ')
        fh.write(str(mean_num/10))
        fh.write(' ')
        fh.write(str(sum(bba.throughputs) / len(bba.throughputs)))
        fh.write(' ')
        fh.write(str(sum(bba.error_rates) / len(bba.error_rates)))
        fh.write(' ')
        fh.write(str(bba.latency/10**12))
        fh.write('\n')

        #print(ls.photon_counter)
        #print(ls.pulse_id)
        #print(qsd.detectors[0].photon_counter)
        #print(qsd.detectors[1].photon_counter)
        #print(bbb.discard)
        #print(bba.throughput)
        #print(bba.key_counter)

    fh.close()