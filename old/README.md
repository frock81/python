gen\_template.py: generates daemons jinja2 template2.

Examples:

    scripts $ ./gen_template.py -i daemon_director.yaml -d spei_bacula___director_config
    scripts $ ./gen_template.py -i daemon_storage.yaml -d spei_bacula___storage_config | less
    scripts $ ./gen_template.py -i daemon_client.yaml -d spei_bacula___client_config | tee ../templates/bacula-fd.conf.j2