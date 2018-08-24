#!/usr/bin/env python

import subprocess
import sys
import argparse
import re
from string import Template

if len(sys.argv) < 2:
	print 'Pipeline must contain two or more stages'
	sys.exit(1) # abort because of error

def stage_type(x, pat = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?")):
 	# regex used for validation is '[a-z0-9]([-a-z0-9]*[a-z0-9])?')
	if not pat.match(x):
 		print 'Project names may only contain lower-case letters, numbers, and dashes. They may not start or end with a dash.'
		sys.exit(1) 
	return x

def jenkins_func(args):

	print 'jenkins pipeline...'

	child = subprocess.Popen('oc get projects',shell=True,stdout=subprocess.PIPE)
	output = child.communicate()[0]

	# Check existing project names
	if args.cicdname in output:
		print "cicd project name " + args.cicdname + " already exist, choose another name, exit"
		sys.exit(1)

	for arg in args.stages:
		stage = arg + " "
		if stage in output:
			print "project " + arg + " already exist, choose another name, exit"
			sys.exit(1)

	# Create & deploy Jenkins
	subprocess.call("oc new-project " + args.cicdname, shell=True)
	subprocess.call("oc project " + args.cicdname, shell=True)
	subprocess.call("oc new-app jenkins-persistent", shell=True)

	# Create service account
	for arg in args.stages:
		subprocess.call("oc new-project " + arg, shell=True)
		subprocess.call("oc policy add-role-to-user edit system:serviceaccount:" + args.cicdname + ":jenkins -n " + arg, shell=True)
		if args.command:
			subprocess.call(args.command, shell=True)
			try:
				subprocess.call("oc expose svc/" + args.appname, shell=True)
			except:
				pass


	for y in args.stages[2:]:
		subprocess.call("oc policy add-role-to-group system:image-puller system:serviceaccounts:" +args.stages[0]+" -n "+y, shell=True)
	
	print "Provide your Application name. Name must match the application name created in every stages"
	appname = args.appname

	f = open("openshift-template.yaml", "w")
	f.write("apiVersion: v1\n")
	f.write("kind: Template\n")
	f.write("metadata:\n")
	f.write("  creationTimestamp: null\n")
	f.write("  name: pipeline\n")
	f.write("objects:\n")
	f.write("- apiVersion: v1\n")
	f.write("  kind: BuildConfig\n")
	f.write("  metadata:\n")
	f.write("    creationTimestamp: null\n")
	f.write("    labels:\n")
	f.write("      app: pipeline\n")
	f.write("      name: pipeline\n")
	f.write("    name: pipeline\n")
	f.write("  spec:\n")
	f.write("    nodeSelector: {}\n")
	f.write("    output: {}\n")
	f.write("    postCommit: {}\n")
	f.write("    resources: {}\n")
	f.write("    runPolicy: Serial\n")
	f.write("    source:\n")
	f.write("      type: None\n")
	f.write("    strategy:\n")
	f.write("      jenkinsPipelineStrategy:\n")
	f.write("        jenkinsfile: \" node() {\\n")
	
	for stage in args.stages:
		t = Template("stage ('Approve Deploy to $stage'){\\n") 
		f.write(t.substitute(stage = stage))
		t = Template("	timeout(time: 2, unit: 'DAYS') {input message: 'Approve to $stage?'}\\n}\\n\\n")
 		f.write(t.substitute(stage = stage, appname =args.appname))

 		t = Template("stage ('Deploy to $stage'){ \\n")
 		f.write(t.substitute(stage = stage, appname =args.appname))
 		t = Template("	openshiftBuild(namespace: '$stage', buildConfig: '$appname', showBuildlog: \'true\')\\n")
		f.write(t.substitute(stage = args.stages[0], appname =args.appname))
		t = Template("	openshiftDeploy(namespace: '$stage',deploymentConfig: '$appname',replicaCount:'1')\\n}\\n")
		f.write(t.substitute(stage = stage, appname =args.appname))
	f.write("}\"\n")
	f.write("type: JenkinsPipeline\n")
	f.write("triggers:\n")
	f.write("    - github:\n")
	f.write("        secret: secret101\n")
	f.write("      type: GitHub\n")
	f.write("    - generic:\n")
	f.write("        secret: secret101\n")
	f.write("      type: Generic\n")
	f.write("status:\n")
	f.write("    lastVersion: 0\n")

	print "Proceed to deploy your applications on the projects"

	subprocess.call("oc project " + args.cicdname, shell=True)
	try:
		subprocess.call("oc new-app openshift-template.yaml", shell=True)
	except:
		subprocess.call("oc new-app openshift-template.yaml", shell=True)

	# oc start-build pipeline
	return 0

def gocd_func(args):

	print 'GoCD...'
	
	subprocess.call("oc new-project gocd", shell=True)
	subprocess.call("oc project gocd", shell=True)
	subprocess.call("oc new-app -f https://raw.githubusercontent.com/jadedh/openshift-gocd/master/gocd.template.yaml", shell=True)
	return 0

def main():
	FUNCTION_MAP = {'gocd' : gocd_func,
					'jenkins' : jenkins_func }

	parser = argparse.ArgumentParser(description='Build ci/cd pipeline on OpenShift')
	parser.add_argument('--cicd', required= True, choices=FUNCTION_MAP.keys())
	parser.add_argument('cicdname', type= stage_type, help="CICD project name")
	parser.add_argument('--appname', required=True, type= stage_type, help="Application name")
	parser.add_argument('--stages', required=True, type= stage_type, nargs='+',help="stages name for the pipeline")
	parser.add_argument('--command', nargs='+',help="command to run in all new-projects e.g. oc new-app [github]")

	args = parser.parse_args()

	func = FUNCTION_MAP[args.cicd]
	func(args)
	#pep8

if __name__ == '__main__':
	main()



