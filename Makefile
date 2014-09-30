.PHONY: test
test: deps
	flake8 --ignore=F403 *.py tests/
	./runtests

.PHONY: deps
deps: ansible/hacking/test-module .ansiblereqs .pyreqs

ansible/hacking/test-module:
	git clone --depth=1 https://github.com/ansible/ansible.git ansible

.ansiblereqs:
	python -c 'import ansible' 2>/dev/null || pip install ./ansible > $@

.pyreqs:
	pip install -r requirements.txt > $@
