#!/usr/bin/env bash

LB_NAME="lb_"$RANDOM
MEM_CHECK_INTERVAL=10
LISTENERS_AMOUNT=100
ITERATIONS=100
LOG=lbaas_mem_sampler.txt

if [ ! -f "`which wget`" ]
then
  yum install -y wget
fi

if [ ! -f "./memexplore.py" ]
then
  wget https://raw.githubusercontent.com/nmagnezi/memexplore/master/memexplore.py
fi
chmod +x memexplore.py

if [ ! -f "/root/keystonerc_admin" ]
then
  # in a case we run on OSP (deployed with packstack)
  source /opt/stack/devstack/openrc admin admin
else
  # in a case we run on devstack
  source /root/keystonerc_admin
fi


echo `date +"%H:%M:%S"` " Starting, the output will also get logged to " $LOG | tee $LOG
echo `date +"%H:%M:%S"` " Sampling RAM for neutron-server before the first loadbalancer create" | tee -a $LOG
./memexplore.py all neutron-server | grep Total | awk '{print $1 " "$5}' | tee -a $LOG
neutron lbaas-loadbalancer-create --name $LB_NAME private_subnet | tee -a $LOG
sleep 5
echo `date +"%H:%M:%S"` " Sampling RAM for neutron-server after the first loadbalancer create" | tee -a $LOG
./memexplore.py all neutron-server | grep Total | awk '{print $1 " "$5}' | tee -a $LOG


echo "Starting to create listeners" | tee -a $LOG

for i in `seq 0 $ITERATIONS`
do
  echo "Starting Iteration: " $i "/" $ITERATIONS
  ./memexplore.py all neutron-server | grep Total | awk '{print $1 " "$5}' | tee -a $LOG

  # Create Listeners
  for j in `seq 1 $LISTENERS_AMOUNT`
  do
    neutron lbaas-listener-create --loadbalancer $LB_NAME --protocol HTTP --protocol-port $j --name "$LB_NAME"_listener_"$j" -c name --format value | tee -a $LOG
    ./memexplore.py all neutron-server | grep Total | awk '{print $1 " "$5}' | tee -a $LOG
    echo `date +"%H:%M:%S"` " Amount of created listeners: " $(( $i*10 + $j )) | tee -a $LOG

    sleep 2
  done

  # Delete Listeners
  for k in `seq 1 $LISTENERS_AMOUNT`
  do
    neutron lbaas-listener-delete "$LB_NAME"_listener_"$k" | tee -a $LOG
    echo `date +"%H:%M:%S"` " Amount of deleted listeners: " $(( $i*10 + $k )) | tee -a $LOG
    ./memexplore.py all neutron-server | grep Total | awk '{print $1 " "$5}' | tee -a $LOG
    sleep 2
  done

done
neutron lbaas-loadbalancer-delete $LB_NAME | tee -a $LOG
echo "All Done"  | tee -a $LOG
echo `date +"%H:%M:%S"` " Sampling RAM for neutron-server after the first loadbalancer create" | tee -a $LOG
