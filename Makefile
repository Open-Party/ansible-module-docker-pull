.PHONY: test
test: deps
	./runtests

.PHONY: deps
deps: ansible/hacking/test-module

ansible/hacking/test-module:
	git clone --depth=1 https://github.com/ansible/ansible.git ansible
