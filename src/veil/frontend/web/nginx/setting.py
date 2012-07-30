from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment.layout import *

nginx_config_file = VEIL_ETC_DIR / 'nginx.conf'
NGINX_BASE_SETTINGS = objectify({
    'nginx': {
        'log_directory': VEIL_LOG_DIR / 'nginx',
        'config_file': nginx_config_file,
        'uploaded_files_directory': VEIL_VAR_DIR / 'uploaded-files',
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static'
    },
    'supervisor': {
        'programs': {
            'nginx': {
                'command': 'veil frontend web nginx up'
            }
        }
    }
})

def create_nginx_server_settings(backend_host, backend_port):
    return {
        'demo.dev.dmright.com': {
            'listen': '127.0.0.1:80',
            'locations': {
                '/': {
                    '_': """
                        if ($content_type ~* multipart/form-data) {
                            upload_pass @after_upload;
                            upload_store %s 1;
                            upload_set_form_field $upload_field_name.name "$upload_file_name";
                            upload_set_form_field $upload_field_name.content_type "$upload_content_type";
                            upload_set_form_field $upload_field_name.path "$upload_tmp_path";
                            upload_pass_args on;
                            upload_pass_form_field "^.*$";
                            upload_cleanup 400-599;
                            break;
                        }
                        proxy_pass http://%s:%s;
                        proxy_set_header   Host             $host;
                        proxy_set_header   X-Real-IP        $remote_addr;
                        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                        """ % (
                        NGINX_BASE_SETTINGS.nginx.uploaded_files_directory,
                        backend_host,
                        backend_port),
                    },
                '@after_upload': {
                    'proxy_pass': 'http://{}:{}'.format(backend_host, backend_port)
                },
                # inline static files
                # /static/v-xxxx/a-b.js
                '~ ^/static/v-(.*)/': {
                    'alias': NGINX_BASE_SETTINGS.nginx.inline_static_files_directory / '$1',
                    'expires': '365d'
                },
                # external static files
                # /static/a/b/c.js?v=xxxx
                '/static/': {
                    '_': """
                        if ($args ~* v=(.+)) {
                            expires 365d;
                        }
                        """,
                    'alias': NGINX_BASE_SETTINGS.nginx.external_static_files_directory / ''
                }
            }
        }
    }