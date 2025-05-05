## Timezone

If the `timezone` field is not provided as part of the config, the program will use the default value `local`. Valid options for `timezone` are:

- `local`: local tz determined from asset's geometry.
- `utc`: utc
- timezone information compatible with `pytz.all_timezones`.

This affects datetime information associated with the project, including:

- `item.datetime` from `collection_date` and `collection_time`.
- Date information from date columns in the asset.

Please refer to this [documentation]() on how time data is processed.

## Collection Metadata

Collection metadata can be provided for serialisation as part of the command line. The supported metadata for collection includes:

- `id`: collection's id
- `title`: collection's title
- `description`: collection's description
- `license`: collection's license

For instance, to serialise items described in a file `config.json` with additional id, title, description and license information, we can run the following command:

```bash
stac_generator serialise config.json\
    --id CollectionID \
    --title CollectionTitle \
    --description CollectionDescription \
    --license MIT\
```

## Serialisation Destination

Serialisation option is provided in the command line through the flag `--dst`, specifying the location where the serialised STAC metadata will be stored. The default value for
dst is `generated`, which creates the folder `generated` in the current directory. Users can provide either a local location to dst, or a [STAC API](https://github.com/radiantearth/stac-api-spec) compliant url, in which
case the metadata will be stored behind an api server. Assuming there exists a STAC API server whose endpoint is `http:102.9.0.32:8082`. To serialise a collection described in `config.json` to this destination, we can run:

```bash
stac_generator serialise config.json
```
