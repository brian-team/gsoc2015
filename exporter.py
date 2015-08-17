from brian2 import *
from brian2.groups.neurongroup import NeuronGroup
import lems.api as lems
from lems.model.component import Constant,ComponentType,Component,FatComponent,Parameter
from lems.model.dynamics import *
from lems.model.model import *

def export_to_lems(_input, _output):
	exec('from ' + _input + ' import *')
	mycomp = ComponentType(_input)

	for o in net.objects:
		if (type(o) is NeuronGroup):

			for i in o.namespace:
				s = str(o.namespace[i])
				l = s.split(".")
				if(len(l))>1:
					l=l[1].strip()
				else:
					l='1'
				myparam = Parameter(i, l)
				mycomp.add_parameter(myparam)

			mydyn = Dynamics()

			if(o._refractory):
				int_regime = Regime('integrating', mydyn, True)
				mydyn.add_regime(int_regime)
				ref_regime = Regime('refractory', mydyn)
				mydyn.add_regime(ref_regime)
				ref_oc = OnCondition('t .gt. ' + str(o._refractory))
				ref_trans = Transition("integrating")
				ref_oc.add_action(ref_trans)
				ref_regime.add_event_handler(ref_oc)
				ref_oe = OnEntry()
				s = str(o.event_codes['spike'])
				l = s.split("=")
				ref_sa = StateAssignment(l[0],l[1])
				ref_oe.add_action(ref_sa)
				ref_regime.add_event_handler(ref_oe)

			for eq in o.user_equations._equations:
				if(o.user_equations._equations[eq].type=='differential equation'):
					mytd = TimeDerivative(str(o.user_equations._equations[eq].varname), str(o.user_equations._equations[eq].expr))
					int_regime.add_time_derivative(mytd)
					thresh_condition = o.events['spike']
					int_oc = OnCondition(thresh_condition.replace('>', '.gt.'))
					int_trans = Transition("refractory")
					int_evout = EventOut("spike")
					int_oc.add_action(int_trans)
					int_oc.add_action(int_evout)
					int_regime.add_event_handler(int_oc)

			mycomp.dynamics = mydyn	
			my_model = Model()
			my_model.add_component_type(mycomp)
			my_model.export_to_file(_output + '.xml')
		
export_to_lems('IF', 'IF_lems')