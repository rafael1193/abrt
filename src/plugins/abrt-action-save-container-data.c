/*
    Copyright (C) 2015  ABRT Team
    Copyright (C) 2015  RedHat inc.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/
#include "libabrt.h"
#include <json/json.h>

void dump_docker_info(struct dump_dir *dd)
{
    char *mntnf_path = concat_path_file(dd->dd_dirname, "mountinfo");
    FILE *mntnf_file = fopen(mntnf_path, "r");
    free(mntnf_path);

    /* Leaking ... */
    struct mountinfo mntnf;
    int r = get_mountinfo_for_mount_point(mntnf_file, &mntnf, "/");
    fclose(mntnf_file);

    if (r != 0)
    {
        error_msg("dockerized processes must have re-mounted root");
        goto dump_docker_info_cleanup;
    }

    const char *mnt_src = MOUNTINFO_MOUNT_SOURCE(mntnf);
    const char *last = strrchr(mnt_src, '/');
    if (last == NULL || strncmp("/docker-", last, strlen("/docker-")) != 0)
    {
        error_msg("Mounted source is not a docker mount source");
        goto dump_docker_info_cleanup;
    }

    last = strrchr(last, '-');
    if (last == NULL)
    {
        error_msg("The docker mount source has unknown format");
        goto dump_docker_info_cleanup;
    }

    ++last;
    char *container_id = xstrndup(last, 12);
    if (strlen(container_id) != 12)
    {
        error_msg("Failed to get container ID");
        goto dump_docker_info_cleanup;
    }

    dd_save_text(dd, "container_id", container_id);

    char *docker_inspect_cmdline = xasprintf("docker inspect %s", container_id);
    log("docker commnad: '%s'", docker_inspect_cmdline);
    char *output = run_in_shell_and_save_output(0, docker_inspect_cmdline, "/", NULL);
    free(docker_inspect_cmdline);

    if (output == NULL)
    {
        error_msg("Failed to introspect the container");
        goto dump_docker_info_cleanup;
    }

    dd_save_text(dd, "docker_introspect", output);

    json_object *json = json_tokener_parse(output);
    if (is_error(json))
    {
        error_msg("fatal: unable parse response from docker  server");
        goto dump_docker_info_cleanup;
    }

    json_object *container = json_object_array_get_idx(json, 0);

    json_object *config = NULL;
    json_object_object_get_ex(container, "Config", &config);

    json_object *image = NULL;
    json_object_object_get_ex(config, "Image", &image);

    char *name = strtrimch(xstrdup(json_object_to_json_string(image)), '"');
    dd_save_text(dd, "container_image", name);
    free(name);

    json_object_put(json);
    free(output);

dump_docker_info_cleanup:
    return;
}

void dump_lxc_info(struct dump_dir *dd, const char *lxc_cmd)
{
}

int main(int argc, char **argv)
{
    /* I18n */
    setlocale(LC_ALL, "");
#if ENABLE_NLS
    bindtextdomain(PACKAGE, LOCALEDIR);
    textdomain(PACKAGE);
#endif

    abrt_init(argv);

    const char *dump_dir_name = ".";

    /* Can't keep these strings/structs static: _() doesn't support that */
    const char *program_usage_string = _(
        "& [-v] -d DIR\n"
        "\n"
        "Query package database and save package and component name"
    );
    enum {
        OPT_v = 1 << 0,
        OPT_d = 1 << 1,
    };
    /* Keep enum above and order of options below in sync! */
    struct options program_options[] = {
        OPT__VERBOSE(&g_verbose),
        OPT_STRING('d', NULL, &dump_dir_name, "DIR"     , _("Problem directory")),
        OPT_END()
    };
    /*unsigned opts =*/ parse_opts(argc, argv, program_options, program_usage_string);

    export_abrt_envvars(0);

    struct dump_dir *dd = dd_opendir(dump_dir_name, /* for writing */0);
    if (dd == NULL)
        xfunc_die();

    char *init_cmdline = dd_load_text_ext(dd, FILENAME_INIT_CMDLINE, DD_LOAD_TEXT_RETURN_NULL_ON_FAILURE);
    if (init_cmdline == NULL)
        error_msg_and_die("The crash didn't occur in container");

    if (strstr("/docker ", init_cmdline) == 0)
        dump_docker_info(dd);
    else if (strstr("/lxc-", init_cmdline) == 0)
        dump_lxc_info(dd, init_cmdline);
    else
        error_msg_and_die("Unsupported container technology");

    dd_close(dd);

    return 0;
}
