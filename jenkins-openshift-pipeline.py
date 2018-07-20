#!/usr/bin/env python

import subprocess

#Setup pipeline projects on OpenShift Account
# 1. cicd
# 2. development
# 3. testing
# 4. production

subprocess.call("oc new-project cicd", shell=True)

subprocess.call("oc new-project development ", shell=True)

subprocess.call("oc new-project testing", shell=True)

subprocess.call("oc new-project production", shell=True)

subprocess.call("oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n development ", shell=True)

subprocess.call("oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n testing ", shell=True)

subprocess.call("oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n production ", shell=True)

subprocess.call("oc policy add-role-to-group system:image-puller system:serviceaccounts:testing -n development", shell=True)

subprocess.call("oc policy add-role-to-group system:image-puller system:serviceaccounts:production -n development", shell=True)

#Deploy Jenkins (persistent)
subprocess.call("oc project cicd", shell=True)

subprocess.call("oc new-app jenkins-persistent", shell=True)

#Create jenkins pipeline from template
#Build-->Deploy in Development-->Approve Deploy to Testing--> Deploy in Testing--> Approve Deploy to Production--> Deploy in Production

subprocess.call("oc new-app -f https://raw.githubusercontent.com/jadedh/jenkins-openshift-pipeline/master/jenkins-openshift-pipeline-template.yaml", shell=True)

print "Proceed to deploy your applications on the projects"

