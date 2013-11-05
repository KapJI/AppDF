all: requirements webkit-server #samples

requirements:
	pip install -r requirements.txt

webkit-server:
	cd webkit-server && python setup.py install

#samples:
#	wget https://github.com/onepf/AppDF/archive/master.tar.gz
#	tar xf master.tar.gz
#	mv AppDF-master/samples samples
#	rm -r AppDF-master
#	rm master.tar.gz

pep8:
	pep8 bin lib
