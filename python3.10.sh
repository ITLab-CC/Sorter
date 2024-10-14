#bin/bash!
screen -mds python10
cd /home/pi/project-teachable-sorter

export SPINNAKER_GENTL64_CTI=/opt/spinnaker/lib/spinnaker-gentl/Spinnaker_GenTL.cti

source py3.10/bin/activate

cd Sorter

python capture_process.py

