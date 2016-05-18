import lems.api as lems
from brian2 import *
from brian2.equations.equations import SingleEquation
from brian2.equations.codestrings import Expression

from lems.model.component import ComponentType,Component

class LEMSBrian:

    def __init__(self, filepath):

        self.component_list = self.get_components_from_file(filepath)
        """ List of all the components in the file
        @type: LEMSBrianComponent """

        self.component_type_list = self.get_component_types_from_file(filepath)
        """ List of all the component types in the file
        @type: LEMSBrianComponentType """

    def get_component_type(self, name):
        a = self.component_list[name]
        b = a.type
        return self.component_type_list[b]

    def get_model_from_file(self, filepath):
        """ @type: lems.model.model.Model"""
        m = lems.Model()
        m.add_include_directory('/home/snigdha/neuroml_dev/NeuroML2/NeuroML2CoreTypes')
        m.import_from_file(filepath)
        return m

    def get_components_from_file(self, filepath):
        """ Imports the file as a model and returns its components """
        mod = self.get_model_from_file(filepath)
        comp = mod.components
        compdict = {}
        for c in comp:
            c.__class__ = LEMSBrianComponent
            compdict[c.id] = c
        return compdict

    def get_component_types_from_file(self, filepath):
        """ Imports the file as a model and returns its component_types """
        mod = self.get_model_from_file(filepath)
        comptypes = mod.component_types
        comptypedict = {}
        for c in comptypes:
            c.__class__ = LEMSBrianComponentType
            comptypedict[c.name] = c
        return comptypedict

class LEMSBrianComponent(Component):

    def __init__(self, id_, type_, **params):
        Component.__init__(self, id_, type_, **params)

class LEMSBrianComponentType(ComponentType):

    def __init__(self, name):
        ComponentType.__init__(self, name)
        self.uf = None

    def get_neurongroup(self, size):
        """ Creates a NeuronGroup of the component with id component_name
        @type: brian2.groups.neurongroup.NeuronGroup """
        model = self.get_equations()
        _threshold = self.get_threshold()
        _reset = self.get_reset()
        _refractory = self.get_refractory()
        N = size
        neuron_group = NeuronGroup(N, model, threshold = _threshold, reset = _reset, refractory = _refractory)
        return neuron_group

    def get_equations(self):
        """ Returns the Equations of the component with id component_name
        @type: brian2.equations.equations.Equations """
        dyn = self.dynamics
        tds = dyn.time_derivatives
        eqs = []
        _flags=[]
        if(tds):
            for t in tds:
                ex = Expression(t.value)
                self.get_refractory()
                for i in self.uf:
                    if(self.uf==t):
                        _flags=['unless refractory']
                s = SingleEquation('differential equation', t.variable, self.timederivative_dimension(t), 'float', ex, flags=_flags)
                eqs.append(s)


        rgs = dyn.regimes
        for r in rgs:
            rtds = r.time_derivatives
            if(rtds):
                for rtd in rtds:
                    ex = Expression(rtd.value)
                    self.get_refractory()
                    for i in self.uf :
                        if(i==rtd):
                            _flags=['unless refractory']
                    s = SingleEquation('differential equation', rtd.variable, self.timederivative_dimension(rtd), 'float', ex, flags=_flags)
                    eqs.append(s)
        dvs = dyn.derived_variables
        for d in dvs:
            if(d.value):
                ex = Expression(d.value)
                s = SingleEquation('subexpression', d.name, self.getBrianSIUnits(d.dimension), 'float', ex)
                eqs.append(s)
        return Equations(eqs)


    def timederivative_dimension(self, TimeDerivative):
        """ Converts the TimeDerivative object into a string and return it
        @type: str """
        svs = self.dynamics.state_variables
        d = None
        for s in svs:
            if(TimeDerivative.variable==s.name):
                d = s.dimension
                td_dim=self.getBrianSIUnits(d)
        return td_dim

    def getBrianSIUnits(self, dimension):
        if(dimension=="voltage"): return volt;
        if(dimension=="conductance"): return siemens;
        if(dimension=="time"): return second;
        if(dimension=="per_time"): return 1/second;
        if(dimension=="capacitance"): return farad;
        if(dimension=="current"): return amp;
        if(dimension=="current"): return amp;
        if(dimension=="volume"): return meter3;
        if(dimension=="concentration"): return mmole;

    def getUnitSymbol(self, dimension):
        if(dimension=="voltage"): return "V";
        if(dimension=="conductance"): return "S";
        if(dimension=="time"): return "s";
        if(dimension=="per_time"): return "1/s";
        if(dimension=="capacitance"): return "F";
        if(dimension=="current"): return "A";
        if(dimension=="volume"): return "m";
        if(dimension=="concentration"): return "mol";

    def replace_operators(self, line):
        line = line.replace(".gt." , ">")
        line = line.replace(".lt." , "<")
        line = line.replace(".leq." , "<=")
        line = line.replace(".geq." , ">=")
        line = line.replace(".eq." , "==")
        line = line.replace(".neq." , "!=")
        line = line.replace(".and." , "and")
        line = line.replace(".or." , "or")
        return line



    def get_threshold(self):
        """ returns the threshold conditions as a string if present otherwise, returns threshold=None
        @type: str"""
        rgs = self.dynamics.regimes
        for r in rgs:
            if(r.initial==True): main_regime = r
            elif(r.initial==False): refractory_regime = r
        roc = main_regime.event_handlers
        threshcond = ""
        for oc in roc:
            if(type(oc) is lems.OnCondition):
                threshcond = self.replace_operators(oc.test)
            else: threshcond=None
        return threshcond


    def get_reset(self):
        """ returns a multi string with the reset statements if present, otherwise returns reset=None
        @type: str"""
        resetcond = ""
        # OnConditions in dynamics
        dyn = self.dynamics
        for ev in dyn.event_handlers:
            if(type(ev) is lems.OnCondition):
                for sa in ev.actions:
                    if(type(sa) is lems.StateAssignment):
                        resetcond+=sa.variable + " = " + sa.value + "\n"

        rgs = self.dynamics.regimes
        for r in rgs:
            if(r.initial==True): main_regime = r
            elif(r.initial==False): refractory_regime = r
        # OnConditions in main regimes
        roc = main_regime.event_handlers
        for oc in roc:
            if(type(oc) is lems.OnCondition):
                for sa in oc.actions:
                    if(type(sa) is lems.StateAssignment):
                        resetcond+=sa.variable + " = " + sa.value + "\n"
        # OnEntry in refractory regime
        roe = refractory_regime.event_handlers
        for oe in roe:
            if(type(oe) is lems.OnEntry):
                for sa in oe.actions:
                    if(type(sa) is lems.StateAssignment):
                        resetcond+=sa.variable + " = " + sa.value + "\n"

        return resetcond


    def get_refractory(self):
        """ return the refractory conditions if present, otherwise returns refractory=None
        @type: str"""
        #OnCondition in refractory regime
        rgs = self.dynamics.regimes
        if len(rgs)>2 :
            raise NotImplementedError("More than 2 regimes are not supported")
        else :
            refract = ""
            for r in rgs:
                if(r.initial==True): main_regime = r
                elif(r.initial==False): refractory_regime = r
            if(refractory_regime.time_derivatives):
                for i in refractory_regime.time_derivatives:
                    if not (i.variable in main_regime.time_derivatives):
                        raise NotImplementedError
            else:
                self.uf=main_regime.time_derivatives

            roc = refractory_regime.event_handlers
            for oc in roc:
                if(type(oc) is lems.OnCondition):
                    refract = "not(" + self.replace_operators(oc.test) + ")"
                    return refract
                else:
                    refract = None
        return refract
