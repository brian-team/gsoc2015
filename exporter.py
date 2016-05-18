from brian2 import *
from brian2.groups.neurongroup import NeuronGroup
from brian2.core.network import *
import lems.api as lems
from lems.model.component import Constant,ComponentType,Component,FatComponent,Parameter
from lems.model.dynamics import *
from lems.model.model import *
import re

def export_to_lems(network, _output):

    if (type(network) is not Network):
        net = Network(collect(level=1))
    else:
        net = network

    for o in net.objects:
        comp = ComponentType(o.name)
        if (type(o) is NeuronGroup):

            for i in o.namespace:
                s = str(o.namespace[i])
                l = s.split(".")
                if(len(l))>1:
                    l=dimension(l[1].strip())
                else:
                    l='none'
                param = Parameter(i, (l))
                comp.add_parameter(param)

            dyn = Dynamics()

            if(o._refractory):
                int_regime = Regime('integrating', dyn, True)
                dyn.add_regime(int_regime)
                ref_regime = Regime('refractory', dyn)
                dyn.add_regime(ref_regime)
                ref_oc = OnCondition('t .gt. ' + purge(str(o._refractory)))
                ref_trans = Transition("integrating")
                ref_oc.add_action(ref_trans)
                ref_regime.add_event_handler(ref_oc)
                if('spike' in o.event_codes):
                    ref_oe = OnEntry()
                    s = str(o.event_codes['spike'])
                    l = s.split("=")
                    ref_sa = StateAssignment(l[0],l[1])
                    ref_oe.add_action(ref_sa)
                    ref_regime.add_event_handler(ref_oe)

            if('spike' in o.events):
                thresh_condition = o.events['spike']
                oc = OnCondition(purge(replace_expr(thresh_condition)))
                evout = EventOut("spike")
                oc.add_action(evout)
                if('spike' in o.event_codes):
                    s = str(o.event_codes['spike'])
                    l = s.split("=")
                    sa = StateAssignment(l[0],l[1])
                    oc.add_action(sa)
                    dim = l[1].split("*")
                    sv = StateVariable(l[0].strip(),dimension(dim[1]))
                    dyn.add_state_variable(sv)

            for eq in o.user_equations._equations:
                if(o.user_equations._equations[eq].type=='differential equation'):
                    td = TimeDerivative(str(o.user_equations._equations[eq].varname), replace_expr(str(o.user_equations._equations[eq].expr)))
                    for svs in dyn.state_variables:
                        if(svs.name!=str(o.user_equations._equations[eq].varname)):
                            sv = StateVariable(str(o.user_equations._equations[eq].varname), dimension(str(o.user_equations._equations[eq].unit)))
                            dyn.add_state_variable(sv)

                    if(o._refractory):
                        int_regime.add_time_derivative(td)
                        int_trans = Transition("refractory")
                        oc.add_action(int_trans)
                        int_regime.add_event_handler(oc)
                    else:
                        dyn.add_time_derivative(td)
                        dyn.add_event_handler(oc)

                if(o.user_equations._equations[eq].type=='subexpression' or o.user_equations._equations[eq].type=='parameter'):
                    dv = DerivedVariable(str(o.user_equations._equations[eq].varname))
                    dv.value = str(o.user_equations._equations[eq].expr)
                    dv.dimension = dimension(str(o.user_equations._equations[eq].unit))
                    dyn.add_derived_variable(dv)


            comp.dynamics = dyn
            model = Model()
            model.add_component_type(comp)
            model.export_to_file(_output + '_lems.xml')

def dimension(unit):
    if('V' in unit) : return 'voltage'
    if('s' in unit) : return 'time'
    if('S' in unit) : return 'conductance'
    if('F' in unit) : return 'capacitance'
    if('per_' in unit) : return 'per_time'
    if('A' in unit) : return 'current'

def replace_expr(expression):
    expression = expression.replace(">", ".gt.")
    expression = expression.replace("<", ".lt.")
    expression = expression.replace("<=", ".leq.")
    expression = expression.replace(">=", ".geq.")
    expression = expression.replace("==", ".eq.")
    expression = expression.replace("!=", ".neq.")
    expression = expression.replace("and", ".and.")
    expression = expression.replace("or", ".or.")
    expression = expression.replace("**", "^")
    return expression

def purge(st):
    st = re.sub(r'(\d+?\.)(?:\s*)?\*(?:\s*)(\w+)', '\\1\\2' , st)
    st = re.sub(r'(\d+?)(?:\s*)?\*(?:\s*)(\w+)', '\\1\\2' , st)
    return st
