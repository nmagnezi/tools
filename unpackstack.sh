#!/bin/bash
#
# This script removes openstack packages from nodes parsed from packstack answers file.
#
# Usage: ./<script_name>.sh --answer-file=<answers file>
# Example: ./unpackstack.sh --answer-file=ans.txt
#

printUsage()
{ # Check script usage
   echo
   echo This script removes openstack packages from nodes parsed from packstack answers file.
   echo
   echo "Usage: $0 --answer-file=<answers file>"
   echo "Usage example: $0 --answer-file=ans.txt"
   echo
}

generateCleanerScript()
{ # Create a tmp script to copy.
  echo
  echo 'Generating Cleaner Script To Copy.'
  echo
  echo '#!/bin/bash' > /tmp/tmpcleaner.sh
  echo 'echo Removing OpenStack Packages' >> /tmp/tmpcleaner.sh
  echo 'yum remove -y *openstack* *nova* *keystone* *glance* *cinder* *swift* qpid-cpp* python-qpid puppet novnc mysql mysql-server httpd perl-DBI perl-DBD-MySQL' >> /tmp/tmpcleaner.sh
  echo 'ps -ef | grep -i repli | grep swift | awk '{print \$2}' | xargs kill' >> /tmp/tmpcleaner.sh
  echo 'umount /srv/node/device*' >> /tmp/tmpcleaner.sh
  echo 'killall dnsmasq &> /dev/null' >> /tmp/tmpcleaner.sh
  echo 'echo Stopping Running Instances' >> /tmp/tmpcleaner.sh
  echo 'for x in \$(virsh list --all | grep instance- | awk '{print \$2}') ; do virsh destroy $x ; virsh undefine $x ; done ;' >> /tmp/tmpcleaner.sh
  echo 'echo Removing Folders' >> /tmp/tmpcleaner.sh
  echo 'pushd /var/ > /dev/null && for svc in nova glance cinder keystone puppet; do   rm -rf $svc ; done && popd > /dev/null' >> /tmp/tmpcleaner.sh
  echo 'pushd /var/lib > /dev/null && for svc in nova glance cinder keystone puppet openstack-dashboard mysql qpid; do   rm -rf $svc ; done && popd > /dev/null' >> /tmp/tmpcleaner.sh
  echo 'pushd /etc/ > /dev/null && for svc in nova glance cinder keystone puppet swift openstack-dashboard; do   rm -rf $svc; done'  >> /tmp/tmpcleaner.sh
  echo 'rm -f /root/.my.cnf' >> /tmp/tmpcleaner.sh
  echo 'rm -f /root/keystonerc*' >> /tmp/tmpcleaner.sh
  echo 'rm -f /var/log/swift-startup.log' >> /tmp/tmpcleaner.sh
  echo 'rm -f /srv/node/device*/*' >> /tmp/tmpcleaner.sh
  chmod +x /tmp/tmpcleaner.sh
}
           
parseAnswersFile() 
{ # Parse packstack answers file for IP Addresses
  local OSHosts=$(cat $1 | grep HOST | cut -d= -f 2 | tr ',' '\n' | sort | uniq)
  echo $OSHosts
}

cleanUp()
{ # Delete cleaner script 
  rm -f /tmp/tmpcleaner.sh
  echo
  echo 'All Done!' 
  echo
}

###################################################
#                      Main                       #
###################################################

# Check that the script is running by root
if [ $UID -ne 0 ] ; then 
   echo
   echo ERROR: You must be root to run this script.
   echo
   exit 1
fi

# Script Usage & Help
if [ $# -ne 1 ] ; then  # Check only 1 parameter
   printUsage $0
   exit 1
fi
if [ $1 = 'h' ] || [ $1 = '-h' ] || [ $1 = 'help' ] || [ $1 = '--help' ] ; then # Script help
   printUsage $0
   exit 0
fi
if [[ $1 != --answer-file=* ]] ; then # Check that the parameter starts with '--answer-file='
   printUsage $0
   exit 1
fi

AnswersFile=$(echo $1 | cut -d= -f 2) # Parse answers file name

if [ ! -f $AnswersFile ] ; then # Check that the answers file exits
   echo
   echo "ERROR: Answers File not found!"
   echo
   exit 1
fi

Hosts=$(parseAnswersFile $AnswersFile) # Extract Hosts from answers file
if [ ! $Hosts ] ; then # Check if there are any extracted hosts from answer file
   echo
   echo "ERROR: Could Not Extract Any Hosts From The Answers File."
   echo 
   exit 1
fi

generateCleanerScript
# Copy & Execute
for i in $Hosts ; do
    echo
    echo 'Working On:' $i
    echo
    scp -p /tmp/tmpcleaner.sh $i:/tmp/
    ssh root@$i /tmp/tmpcleaner.sh 
    ssh root@$i rm -f /tmp/tmpcleaner.sh
done;
cleanUp
