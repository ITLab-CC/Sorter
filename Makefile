.PHONY: all build camera sorter
PYTHON_VERSION_3_10 := $(shell python3.10 --version)
PYTHON_VERSION_3_9 := $(shell python3.9 --version)

all: build

build: camera-build sorter-build start
	echo "Build done."

start: kill camera sorter
	echo "Start done."

install-screen:
	sudo apt install screen -R

install-python3.10:
	@if [ -z "$(PYTHON_VERSION_3_10)" ]; then \
		echo "Python 3.10 is not installed."; \
		echo "install Python 3.10"; \
		sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev; \
		wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tar.xz; \
		tar xf Python-3.10.0.tar.xz; \
		cd Python-3.10.0; \
		./configure --enable-optimizations --prefix=/usr; \
		make; \
		sudo make altinstall; \
		echo "clean up"; \
		cd ..; \
		sudo rm -r Python-3.10.0; \
		rm Python-3.10.0.tar.xz; \
		. ~/.bashrc; \
	else \
		echo "Python 3.10 is installed."; \
	fi

camera-build: install-python3.10
	# Erstellt die virtuelle Umgebung für Camera und startet das Script in Screen
	echo "Setting up Camera environment..."
	mkdir -p ./camera/logs
	@if [ ! -f "./spinnaker.tar.gz" ]; then \
		echo "Download spinnaker"; \
		wget https://flir.netx.net/file/asset/59509/original/attachment -O ./spinnaker.tar.gz; \
	fi
	echo "Extracting and installing spinnaker_python...";
	mkdir -p spinnaker_python;
	tar -xzvf spinnaker.tar.gz -C spinnaker_python;
	python3.10 -m venv ./camera/.venv-3.10
	./camera/.venv-3.10/bin/pip install ./spinnaker_python/spinnaker_python-4.0.0.116-cp310-cp310-linux_aarch64.whl;
	rm -rf spinnaker_python;
	./camera/.venv-3.10/bin/pip install -r ./camera/requirements.txt

camera:
	echo "Starting Camera script in Screen..."
	screen -dmS camera bash -c "source ./camera/.venv-3.10/bin/activate && python -u ./camera/main.py 2>&1 | tee ./camera/logs/output.log"

install-python3.9:
	@if [ -z "$(PYTHON_VERSION_3_9)" ]; then \
		echo "Python 3.9 is not installed."; \
		echo "install Python 3.9"; \
		sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev; \
		wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tar.xz; \
		tar xf Python-3.9.0.tar.xz; \
		cd Python-3.9.0; \
		./configure --enable-optimizations --prefix=/usr; \
		make; \
		sudo make altinstall; \
		echo "clean up"; \
		cd ..; \
		sudo rm -r Python-3.9.0; \
		rm Python-3.9.0.tar.xz; \
		. ~/.bashrc; \
	else \
		echo "Python 3.9 is installed."; \
	fi

sorter-build: install-python3.9
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