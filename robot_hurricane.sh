# this script is used to integrate hurricane deployer with robot tests in one jenkins job.

python hurricane/jenkins.py
python hurricane/main.py

IFS=', ' read -a array <<< "$DEPLOYER_HOSTS_AND_ROLES"

for i in "${array[@]}"
do
    role=`echo "$i" | cut -d"/" -f2`
    if [ $role == 'controller' ] ; then
        controller_fqdn=`echo "$i" | cut -d"/" -f1`
        controller=`dig +short $controller_fqdn`
    fi

    if [ $role == 'networker' ] ; then
        networker_fqdn=`echo "$i" | cut -d"/" -f1`
        networker=`dig +short $networker_fqdn`
    fi

    if [ $role == 'compute' ] ; then
        if [ -z "$compute" ]; then
           compute_fqdn=`echo "$i" | cut -d"/" -f1`
           compute=`dig +short $compute_fqdn`
        else
           tmp_compute_fqdn=`echo "$i" | cut -d"/" -f1`
           tmp_compute=`dig +short $tmp_compute_fqdn`
           compute="$compute,$tmp_compute"
        fi

    fi
done

# Variables
test="robot-hurricane.robot"
report_file="/var/www/html/index.html"
report="yes"
test_server=`dig +short <jenkins_fqdn>`

# Vlans
vlan_start=208
vlan_end=210
cidr=1.2.3.0/24
gateway=1.2.3.254

# Prepare Directory and Link for Robot HTML Log
/bin/mkdir -p ${WORKSPACE}/${BUILD_NUMBER}_logs/
echo Report is in: http://<jenkins_fqdn>:8080/job/${JOB_NAME}/ws/${BUILD_NUMBER}_logs/log.html

# Run Test
pushd $WORKSPACE/storm/tests/
pybot -v product:${DEPLOYER_PRODUCT} -v version:${DEPLOYER_OPENSTACK_VERSION} -v puddle:${DEPLOYER_OPENSTACK_BUILD} -v test_server:${test_server} -v client:$controller -v networking_server:${controller} -v networking_l3:${networker} -v networking_dhcp:${networker} -v networking_metadata:${networker} -v vlan_start:${vlan_start} -v vlan_end:${vlan_end} -v vlan_ext:${DEPLOYER_EXT_VLAN} -v cidr:${cidr} -v gateway:${gateway} -v nova_compute:${compute} -v horizon_ssl:y -v run_tests:yes -x ${WORKSPACE}/${BUILD_NUMBER}_logs/xunit.xml -d ${WORKSPACE}/${BUILD_NUMBER}_logs/ -C ansi ${test} | /usr/bin/tee ${WORKSPACE}/output

#publish
python ${WORKSPACE}/publish_job_report.py ${report_file} ${WORKSPACE}/output ${DEPLOYER_PRODUCT} ${DEPLOYER_OPENSTACK_VERSION} ${DEPLOYER_OPENSTACK_BUILD} ${DEPLOYER_OPERATING_SYSTEM} ${BUILD_NUMBER} ${BUILD_ID} ${report}
