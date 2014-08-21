.PHONY: test
test: deps
	./runtests

.PHONY: deps
deps: ansible/hacking/test-module .ansiblereqs

ansible/hacking/test-module:
	git clone --depth=1 https://github.com/ansible/ansible.git ansible

.ansiblereqs:
	python -c 'import ansible' 2>/dev/null || pip install ./ansible > $@
