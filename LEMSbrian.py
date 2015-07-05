import lems.api as lems
from brian2 import *

class LEMSBrian:

	def __init__(self, filepath):

		self.component_list = self.get_components_from_file(filepath)
		""" Dictionary of all the components in the file
		@type: dict(str -> lems.model.component.Component) """

		self.component_type_list = self.get_component_types_from_file(filepath)
		""" Dictionary of all the component_types in the file
		@type: dict(str -> lems.model.component.ComponentType) """

	def getComponents(self, Model):
		""" @type: dict(str -> lems.model.component.Component)"""
		return Model.components

	def getComponentTypes(self, Model):
		""" @type: dict(str -> lems.model.component.ComponentType)"""
		return Model.component_types

	def getParameters(self, Component):
		""" @type: Map(str -> lems.model.component.Parameter)"""
		return Component.parameters

	def getDynamics(self, ComponentType):
		""" @type: lems.model.dynamics.Dynamics """
		return ComponentType.dynamics

	
	def getTimederivatives(self, Dynamics):
		""" @type: dict(str -> lems.model.dynamics.TimeDerivative)"""
		return Dynamics.time_derivatives

	def getRegimes(self, Dynamics):
		""" @type: Map(str -> lems.model.dynamics.Regime)"""
		return Dynamics.regimes

	def getStatevariables(self, Dynamics):
		""" @type: dict(str -> lems.model.dynamics.StateVariable)"""
		return Dynamics.state_variables

	def getDerivedvaribales(self, Dynamics):
		""" @type: dict(str -> lems.model.dynamics.DerivedVariable)"""
		return Dynamics.derived_variables

	def getEventhandlers(self, Dynamics):
		""" @type: list(lems.model.dynamics.EventHandler)"""
		return Dynamics.event_handlers

	def get_model_from_file(self, filepath):
		""" @type: lems.model.model.Model"""
		m = new lems.Model()
		m.import_from_file(filepath)
		return m
	
	def get_components_from_file(self, filepath):
		""" Imports the file as a model and returns its components """
		mod = self.get_model_from_file(filepath)
		comp = self.getComponents(mod)
		return comp

	def get_component_types_from_file(self, filepath):
		""" Imports the file as a model and returns its component_types """
		mod = self.get_model_from_file(filepath)
		comptypes = self.getComponentTypes(mod)
		return comptypes

	def get_neurongroup(self, component_name):
		""" Creates a NeuronGroup of the component with id component_name
		@type: brian2.groups.neurongroup.NeuronGroup """
		comp = self.get_components_from_file[component_name]
		comp_type = self.get_component_types_from_file[comp.type]
		model = self.get_equations(component_name)
		threshold = self.get_threshold(comp_type)
		reset = self.get_reset(comp_type)
		refractory = self.get_refractory(comp_type)
		name_space = self.get_namespace(comp)
		neuron_group = NeuronGroup(N, model, threshold, reset, refractory, name_space)
		return neuron_group

	def get_equations(self, component_name):
		""" Returns the Equations of the component with id component_name
		@type: brian2.equations.equations.Equations """
		comp = self.get_components_from_file[component_name]
		comp_type = self.get_component_types_from_file[comp.type]
		tds = self.getTimederivatives(comp_type)
		eqs = ""
		for t in tds:
			eqs+=self.timederivative_to_string(t)
		dyn = self.getDynamics(comp_type)
		rgs = self.getRegimes(dyn)
		for r in rgs:
			rtds = self.getTimederivatives(r)
			for rtd in rtds:
				eqs+=self.timederivative_to_string(rtd)
		equations = Equations(eqs)
		return equations


	def timederivative_to_string(self, TimeDerivative):
		""" Converts the TimeDerivative object into a string and return it
		@type: str """

	def get_threshold(self, ComponentType):
		""" returns the threshold conditions as a string if present otherwise, returns threshold=None
		@type: str"""

	def get_reset(self, ComponentType):
		""" returns a multi string with the reset statements if present, otherwise returns reset=None
		@type: str"""

	def get_refractory(self, ComponentType):
		""" return the refractory conditions if present, otherwise returns refractory=None
		@type: str"""

	def get_namespace(self, Component):
		""" returns the parameters of the Component as a dictionary """

