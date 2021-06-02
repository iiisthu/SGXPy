.PHONY: test
test:
	@echo "regression test."
	@echo "================================================================"
	@./tests/test_sgxpython.py
	# @echo "numpy test."
	# @echo "================================================================"
	# @./script/nptestsuite.py

.PHONY: clean
clean:
	@rm -f *.pyc
	@rm -f */*.sgx */*.manifest */*.sig */*.token */*.log*
	@rm -f */*.pyc
	@rm -f */t.py
	@rm -f */_configtest.o.d
	@rm -f *.log
