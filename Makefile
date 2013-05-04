install:
	sudo apt-get install gcc make libmysqlclient-dev
	sudo gcc -fpic -Wall -I/usr/include/mysql -I. -shared lib_mysqludf_sys.c -o /usr/lib/mysql/plugin/lib_mysqludf_sys.so
	mysql -u root -p -e "DROP FUNCTION IF EXISTS sys_exec"
	mysql -u root -p -e "CREATE FUNCTION sys_exec RETURNS int SONAME 'lib_mysqludf_sys.so'"
	python setup.py install
	rm -rf build
