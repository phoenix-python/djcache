#include <my_global.h>
#include <my_sys.h>
#include <mysql.h>
#include <m_ctype.h>
#include <m_string.h>


my_bool sys_exec(UDF_INIT *initid, UDF_ARGS *args, char *is_null, char *error) {
    return system(args->args[0]);
}


my_bool sys_exec_init(UDF_INIT *initid, UDF_ARGS *args, char *message) {
    if (args->arg_count == 1 && args->arg_type[0] == STRING_RESULT)
        return 0;
    strcpy(message, "Wrong arguments");
    return 1;
}
