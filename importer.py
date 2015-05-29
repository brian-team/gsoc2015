import lems.api as lems

fn = 'iaf.xml'
m = lems.Model()
m.import_from_file(fn)

str_list = []
str_list.append("from brian2 import *\n")

for i in range(len(m.components[m.components.keys()[0]].parameters.keys())):
	str_list.append(m.components[m.components.keys()[0]].parameters.keys()[i] + "=" + m.components[m.components.keys()[0]].parameters.values()[i] + "\n")

for i in m.component_types:
	if i.dynamics.time_derivatives:
		for j in i.dynamics.time_derivatives:
			str_list.append("eqs = ''' ")
			str_list.append("d" + j.variable + "/dt = " + j.value)
			str_list.append(" ''' ")
	for j in i.dynamics.regimes:
		if j.time_derivatives:
			for k in j.time_derivatives:
				str_list.append("eqs = ''' ")
				str_list.append("d" + k.variable + "/dt = " + k.value)
				str_list.append(" ''' ")

str_list.append("group = Neurongroup(1, eqs")

for i in m.component_types:
	if i.dynamics.event_handlers:
		for j in i.dynamics.event_handlers:
			if type(j) is lems.OnCondition:
				print j.test
	if i.dynamics.regimes:
		for j in i.dynamics.regimes:
			if j.event_handlers:
				for k in j.event_handlers:
					if type(k) is lems.OnCondition:
						if k.test.startswith("v .gt"):
							str_list.append(", threshold='v >")

with open('output.py', 'w') as out_file:
	out_file.write(''.join(str_list))


