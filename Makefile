.PHONY: all build camera sorter

all: build

build: camera-build sorter-build start
	echo "Build done."

start: kill camera sorter
	echo "Start done."

camera-build:
	# Erstellt die virtuelle Umgebung für Camera und startet das Script in Screen
	echo "Setting up Camera environment..."
	mkdir -p ./camera/logs
	python3.10 -m venv ./camera/.venv-3.10
	@if [ ! -f "./spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz" ]; then \
		echo "Download spinnaker_python: 'https://www.teledynevisionsolutions.com/support/support-center/software-firmware-downloads/iis/spinnaker-sdk-download/spinnaker-sdk--download-files/?pn=Spinnaker+SDK&vn=Spinnaker+SDK' and save it as 'spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz' to this folder."; \
	else \
		echo "Extracting and installing spinnaker_python..."; \
		mkdir -p spinnaker_python; \
		tar -xzvf spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.tar.gz -C spinnaker_python; \
		./camera/.venv-3.10/bin/pip install ./spinnaker_python/spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.whl; \
		rm -rf spinnaker_python; \
	fi
	./camera/.venv-3.10/bin/pip install -r ./camera/requirements.txt

camera:
	echo "Starting Camera script in Screen..."
	screen -dmS camera bash -c "source ./camera/.venv-3.10/bin/activate && python -u ./camera/main.py 2>&1 | tee ./camera/logs/output.log"

sorter-build:
	# Erstellt die virtuelle Umgebung für Sorter und startet das Script in Screen
	echo "Setting up Sorter environment..."
	mkdir -p ./sorter/logs
	python3.9 -m venv ./sorter/.venv-3.9
	./sorter/.venv-3.9/bin/pip install -r ./sorter/requirements.txt

sorter:
	echo "Starting Sorter script in Screen..."
	screen -dmS sorter bash -c "source ./sorter/.venv-3.9/bin/activate && python -u ./sorter/main.py 2>&1 | tee ./sorter/logs/output.log"

kill:
	echo "Killing Screen sessions..."
	@if screen -ls | grep -q "\.camera"; then \
		echo "Stopping screen session 'camera'..."; \
		screen -S camera -X quit; \
	else \
		echo "Screen session 'camera' does not exist."; \
	fi
	@if screen -ls | grep -q "\.sorter"; then \
		echo "Stopping screen session 'sorter'..."; \
		screen -S sorter -X quit; \
	else \
		echo "Screen session 'sorter' does not exist."; \
	fi

stop: kill
	echo "Stop done."

clean: kill
	rm -Rf ./camera/.venv-3.10
	rm -Rf ./sorter/.venv-3.9

clear: clean
	echo "Clear done."