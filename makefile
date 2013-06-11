install:
	sudo apt-get install gcc make libmysqlclient-dev
	sudo gcc -fpic -Wall -I/usr/include/mysql -shared udf.c -o /usr/lib/mysql/plugin/udf.so
	mysql -u root -p -e "DROP FUNCTION IF EXISTS sys_exec"
	mysql -u root -p -e "CREATE FUNCTION sys_exec RETURNS int SONAME 'udf.so'"
