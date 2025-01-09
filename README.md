# stac-generator

Documentation [page](https://aus-plant-phenomics-network.github.io/stac-generator/)

Examples of stac generator [configs](./example/configs/) in csv/json/yaml

Examples of generated stac items for [point]() data, [vector]() data, [raster]() data

## CLI Commands

Generating collection and push to remote

```bash
pdm run stac_generator https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/OZBarley/remote_config.json --dst http://203.101.227.130:8082 --id OZBarleyTestData
```


## For developers

Clone:

```bash
git clone https://github.com/aus-plant-phenomics-network/stac-generator.git
```

Install dependencies:

```bash
pdm install
```

Run tests:

Note that you may need to set the environment variable `REMOTE_FIXTURE_URL` either through commands or via a `.env` file. The value of this variable
can be found on the github [repository](https://github.com/aus-plant-phenomics-network/stac-generator/settings/environments/4607709709/edit) under Settings - Environments - Environment Variables.

```bash
make test
```

Run static analysis

```bash
make lint
```
