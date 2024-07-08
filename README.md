# encpos-app
Elasticsearch API to search the ENC Thesis Abstracts ([Positions de thèses](https://theses.chartes.psl.eu/)).

## Install

- Clone the GitHub repository:  
in a local folder dedicated to the project
```bash
git clone https://github.com/chartes/encpos-app.git
```

- Execute the following commands:  
in the app folder (`cd local/path/to/app_folder`)
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
On a server with python applications served by uWSGI, install uWSGI as required `pip3 install uWSGI`.

- Launch the app using:  
from the app subfolder containing flask_app.py
```bash
python3 flask_app.py
```

## Indexing

### Install an Elasticsearch's version (compatible with requirements.txt specs) 
- Elasticsearch : see https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html#elasticsearch-install-packages  
- ICU plugin : see https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html  
check if ICU is installed with `uconv -V` (currently deployed : uconv v2.1  ICU 63.1), otherwise : 
```bash
sudo {path/to/elasticsearch_folder}/bin/elasticsearch-plugin install analysis-icu
```

With docker (security disabled):
```bash
docker run --name es-encpos -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.http.ssl.enabled=false" elasticsearch:8.12.1
docker exec es-encpos bash -c "bin/elasticsearch-plugin install analysis-icu"
docker restart es-encpos
```

### Initial indexing:
```bash
ES_PASSWORD={ELASTIC_PASSWORD} python3 manage.py update-conf
ES_PASSWORD={ELASTIC_PASSWORD} python3 manage.py index (--years=YYYY-YYYY)
```

### Update the indexes' configuration:
```bash
ES_PASSWORD={ELASTIC_PASSWORD} python3 manage.py update-conf --rebuild
```
The above command updates the indexes according to the ES [configuration](./elasticsearch/).  


### Index or reindex (without configuration changes):
```bash
ES_PASSWORD={ELASTIC_PASSWORD} python3 manage.py index (--years=YYYY-YYYY)
```

### Check created indexes:
```bash
curl http://elastic:{ELASTIC_PASSWORD}@localhost:9200
```

## Launch the front-end:
- [Front-end's Readme](https://github.com/chartes/encpos-vue/blob/dev/README.md)

---
Additional details for offline commands:

```bash
python3 manage.py --help

Usage: manage.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands (will also need ES_PASSWORD environment variable):
  delete       Delete the indexes
  index        Rebuild the elasticsearch indexes
  search       Perform a search using the provided query.
  update-conf  Update the index configuration and mappings

```
