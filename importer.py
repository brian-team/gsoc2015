import lems.api as lems
from lems.model.component import *
from brian2 import *

m = lems.Model()
m.add_include_directory('/home/snigdha/neuroml_dev/NeuroML2/NeuroML2CoreTypes')

def getComponents(Model):
	return Model.components

def getParameters(Component):
	return Component.parameters

def getDynamics(ComponentType):
	return ComponentType.dynamics

def getExposures(ComponentType):
	return ComponentType.exposures

def getChildren(ComponentType):
	return ComponentType.children

def getTimederivatives(Dynamics):
	return Dynamics.time_derivatives

def getRegimes(Dynamics):
	return Dynamics.regimes

def getStatevariables(Dynamics):
	return Dynamics.state_variables

def getDerivedvaribales(Dynamics):
	return Dynamics.derived_variables

def getEventhandlers(Dynamics):
	return Dynamics.event_handlers

def tobrian(filepath):
	s = ""
	m.import_from_file(filepath)
	comp = getComponents(m)
	for c in comp:
		name_space = "{"
		params = getParameters(c)
		first = True
		for p in params:
			if(first!=True):
				name_space+=", "
			name_space+="'" + p + "' : " + params.get(p)
			first=False
		name_space+= "}"
		ct = m.component_types[c.type]
		dyn = getDynamics(ct)
		svs = getStatevariables(dyn)
		tds = getTimederivatives(dyn)
		eqs = "Equations('''\n"
		if(tds): 
			for t in tds:
				eqs+="    d" + t.variable + "/dt = " + t.value + " : " + "\n"

		rgs = getRegimes(dyn)
		for r in rgs:
			rtds = getTimederivatives(r)
			if(rtds):
				for rt in rtds:
					eqs+="    d" + rt.variable + "/dt = " + rt.value + "\n"
		dvs = getDerivedvaribales(dyn)
		for d in dvs:
			if(d.value):
				eqs+= "    " + d.name + " = "
				eqs+=d.value + "\n"
		eqs+="''')"
		size = 1
		G = "NeuronGroup( 1" + ", model = " + eqs + ", namespace = " + name_space + ")\n"
		print G



tobrian('LEMS_NML2_Ex0_IaF.xml')
