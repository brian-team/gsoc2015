from brian2 import *
from exporter import *
import sys

# n = 1000
duration = 1*second
# tau = 10*ms
eqs = '''
dv/dt = (v0 - v) / tau : volt
v0 : volt
'''
n = 1000
_namespace={'n':1000, 'duration':1*second, 'tau':10*ms}
group = NeuronGroup(n, eqs, threshold='v > 10*mV', reset='v = 0*mV',
                    refractory=5*ms, namespace=_namespace)
group.v = 0*mV
group.v0 = '20*mV * i / (n-1)'
print group.equations._equations
net = {}
export_to_lems(net, str(sys.argv[0].split(".")[0]))

monitor = SpikeMonitor(group)
# net = Network(collect())
run(duration)
plot(group.v0/mV, monitor.count / duration)
xlabel('v0 (mV)')
ylabel('Firing rate (sp/s)')
# show()
