import lems.api as lems
from brian2 import *
from lems.base.base import LEMSBase
from lems.base.util import merge_maps, merge_lists
from lems.base.map import Map
from lems.parser.LEMS import LEMSFileParser
from lems.base.errors import ModelError
from lems.base.errors import SimBuildError

from lems.model.fundamental import Dimension,Unit
from lems.model.component import Constant,ComponentType,Component,FatComponent

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

	def get_neurongroup(self):
		""" Creates a NeuronGroup of the component with id component_name
		@type: brian2.groups.neurongroup.NeuronGroup """
		model = self.get_equations()
		threshold = self.get_threshold()
		reset = self.get_reset()
		refractory = self.get_refractory()
		# name_space = self.get_namespace(comp)
		N = 1 # replace later by get_size which will get the population
		neuron_group = NeuronGroup(N, model, threshold)
		return neuron_group

	def get_equations(self):
		""" Returns the Equations of the component with id component_name
		@type: brian2.equations.equations.Equations """
		dyn = self.dynamics
		tds = dyn.time_derivatives
		# eqs = "'''\n"
		eqs=""
		if(tds):
			for t in tds:
				eqs+=self.timederivative_to_string(t)
		
		rgs = dyn.regimes
		for r in rgs:
			rtds = r.time_derivatives
			if(rtds):
				for rtd in rtds:
					eqs+=self.timederivative_to_string(rtd)
		dvs = dyn.derived_variables
		for d in dvs:
			if(d.value):
				eqs+=d.name + " = " + d.value + " : " + self.getBrianSIUnits(d.dimension) + "\n"
		equations = Equations(eqs)
		return equations


	def timederivative_to_string(self, TimeDerivative):
		""" Converts the TimeDerivative object into a string and return it
		@type: str """
		td_eqn = "d" + TimeDerivative.variable + "/dt = " + TimeDerivative.value
		svs = self.dynamics.state_variables
		d = None
		for s in svs:
			if(TimeDerivative.variable==s.name):
				d = s.dimension
				td_eqn+=" : " + self.getBrianSIUnits(d) + "\n"
		return td_eqn

	def getBrianSIUnits(self, dimension):
		if(dimension=="voltage"): return "volt";
		if(dimension=="conductance"): return "siemens";
		if(dimension=="time"): return "second";
		if(dimension=="per_time"): return "1/second";
		if(dimension=="capacitance"): return "farad";
		if(dimension=="current"): return "amp";
		if(dimension=="current"): return "amp";
		if(dimension=="volume"): return "meter3";
		if(dimension=="concentration"): return "mmole";

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
			else: threshcond="None"
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
		refract = ""
		for r in rgs:
			if(r.initial==True): main_regime = r
			elif(r.initial==False): refractory_regime = r
		roc = refractory_regime.event_handlers
		for oc in roc:
			if(type(oc) is lems.OnCondition):
				refract = "not(" + self.replace_operators(oc.test) + ")"
			else: refract = "None"
		return refract

	def get_namespace(self, Component):
		""" returns the parameters of the Component as a dictionary """

model = LEMSBrian('LEMS_NML2_Ex0_IaF.xml')
# print model.component_list
a = model.get_component_type('iafRef')
print a.get_equations()
print a.get_threshold()
print a.get_reset()
print a.get_refractory()
print a.get_neurongroup()