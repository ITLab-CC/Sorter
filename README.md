1. Downloade the python version of the Spinnaker SDK from the following link: 
! DONT USE THE NORMAL VERSION: DOWNLOADE THE PYTHON VERSION !
https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK

2. unpacke:
```bash
mkdir spinnaker_python
tar -xzvf spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz -C spinnaker_python
```

3. install:
```bash
cd spinnaker_python
pip3 install spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.whl
cd ..
rm -rf spinnaker_python
```