# wazo-microsoft plugin

## Deprecated

This plugins has been merged into wazo-auth and wazo-dird avoid using this plugin on a version above wazo 19.10

### auth plugin
This plugin adds routes to manage microsoft authentication.

## Configuration
Theses lines should be added to `wazo-sdk/project.yml` in order to overwrite other configurations. Therefore, the files in `/etc` should also exist.

```yml
wazo-microsoft:
  python3: true
  bind:
    etc/wazo-auth/conf.d/microsoft.yml: /etc/wazo-auth/conf.d/microsoft.yml
```
# Running integration tests
You need Docker installed.

```sh
cd integration_tests
pip install -U -r test-requirements.txt
make test-setup
make test
```
