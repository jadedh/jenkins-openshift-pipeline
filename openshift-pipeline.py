#!/usr/bin/env python

import subprocess
import sys
import argparse
from jinja2 import Environment
from jinja2 import FileSystemLoader


if len(sys.argv) < 2:
	print 'Pipeline must contain two or more stages'
	sys.exit(1) # abort because of error
print "Provide your Application name. Name must match the application name created in every stages"
appname = raw_input("Enter app name:")

# Create & deploy Jenkins
subprocess.call("oc new-project cicd", shell=True)
subprocess.call("oc project cicd", shell=True)
subprocess.call("oc new-app jenkins-persistent", shell=True)

# Create service account
for x in sys.argv[1:]:
	subprocess.call("oc new-project " + x, shell=True)
	subprocess.call("oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n " + x, shell=True)

for y in sys.argv[2:]:
	subprocess.call("oc policy add-role-to-group system:image-puller system:serviceaccounts:" +sys.argv[1]+" -n "+y, shell=True)

j2_env = Environment(loader=FileSystemLoader('templates'),trim_blocks=True)
template = j2_env.get_template('pipeline_template.j2')
rendered_file = template.render(stages=sys.argv,appname=appname)

print(rendered_file)
f= open("pipeline-template.yaml", "w+")
f.write(rendered_file)

print "Proceed to deploy your applications on the projects"

#oc new-app jenkins-template.yaml
#oc start-build pipeline