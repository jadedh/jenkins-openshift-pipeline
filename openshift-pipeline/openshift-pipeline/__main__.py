#!/usr/bin/env python

import subprocess
import sys
import argparse
import re
from jinja2 import Environment
from jinja2 import FileSystemLoader


if len(sys.argv) < 2:
	print 'Pipeline must contain two or more stages'
	sys.exit(1) # abort because of error

def stage_type(x, pat = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?")):
 	# regex used for validation is '[a-z0-9]([-a-z0-9]*[a-z0-9])?')
	if not pat.match(x):
 		print 'Project names may only contain lower-case letters, numbers, and dashes. They may not start or end with a dash.'
		sys.exit(1) 
	return x

def jenkins_func():

	print 'jenkins pipeline instantiated...'

	# Create & deploy Jenkins
	subprocess.call("oc new-project cicd", shell=True)
	subprocess.call("oc project cicd", shell=True)
	subprocess.call("oc new-app jenkins-persistent", shell=True)

	# Create service account
	for arg in args.stages:
		subprocess.call("oc new-project " + arg, shell=True)
		subprocess.call("oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n " + arg, shell=True)

	for y in args.stages[2:]:
		subprocess.call("oc policy add-role-to-group system:image-puller system:serviceaccounts:" +args.stages[0]+" -n "+y, shell=True)
	
	j2_env = Environment(loader=FileSystemLoader('templates'),trim_blocks=True)
	template = j2_env.get_template('pipeline_template.j2')
	
	print "Provide your Application name. Name must match the application name created in every stages"
	appname = raw_input("Enter app name:")
	
	rendered_file = template.render(stages = args.stages, appname = appname)
	print(rendered_file)
	f= open("pipeline-template.yaml", "w+")
	f.write(rendered_file)

	print "Proceed to deploy your applications on the projects"

	#oc new-app jenkins-template.yaml
	#oc start-build pipeline
	return 0

def gocd_func():

	print 'GoCD'
	
	subprocess.call("oc new-project gocd", shell=True)
	subprocess.call("oc project gocd", shell=True)
	subprocess.call("oc new-app -f https://raw.githubusercontent.com/atbentley/openshift-gocd/master/gocd.template.yaml", shell=True)
	return 0

def main():
	FUNCTION_MAP = {'gocd' : gocd_func,
					'jenkins' : jenkins_func }

	parser = argparse.ArgumentParser(description='Build ci/cd pipeline on OpenShift')
	parser.add_argument('command', choices=FUNCTION_MAP.keys())
	parser.add_argument("stages", type= stage_type, nargs='+',help="stages name for the pipeline")

	args = parser.parse_args()

	func = FUNCTION_MAP[args.command]
	func()
	# flak8, pep8

if __name__ == '__main__':
	main()



