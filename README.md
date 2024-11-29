# encpos-app
Elasticsearch API to search the ENC Thesis Abstracts ([Positions de thèses](https://theses.chartes.psl.eu/)).

## Install

- Clone the GitHub repository:  
in a local folder dedicated to the project
  ```bash
  git clone https://github.com/chartes/encpos-app.git
  ```

- Set up the virtual environment:  
in the app folder (`cd path/to/encpos-app`)
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip3 install -r requirements.txt
  ```
  For servers requiring uWSGI to run Python apps (remote Nginx servers):
  - check if uWSGI is installed `pip3 list --local`
  - install it in the virtual env if it's not: `pip3 install uWSGI`.

  *NB : cette commande peut nécessiter d'installer wheel :*  
  - pour vérifier si wheel est installé : `pip3 show wheel`  
  - pour l'installer le cas échéant : `pip3 install wheel`


- Install Elasticsearch and create indices _if they are not available_:  
Follow the ES installation & initial indexing instructions [below](#indexing)  


- Launch the app:
> :warning: Below commands are mainly for local launch.  
> For servers, apps may be started via processes management tools, refer to the servers documentation
  - Reactivate the virtual environment if needed (`source venv/bin/activate`)
  - Launch:  
  from the subfolder containing flask_app.py (`cd path/to/encpos_app`)
    ```bash
    (ES_PASSWORD={ELASTIC_PASSWORD}) python3 flask_app.py
    ```

## Indexing

### Install an Elasticsearch's version (compatible with requirements.txt specs)
> :warning: These commands are run independently/outside the app virtual environment
- Elasticsearch : see internal instructions or https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html#elasticsearch-install-packages   
- ICU plugin : see https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html  
check if ICU is installed with `uconv -V` (currently deployed : uconv v2.1  ICU 63.1), otherwise : 
  ```bash
  {path/to/elasticsearch_folder}/bin/elasticsearch-plugin install analysis-icu
  ```

With docker (security disabled):
```bash
docker run --name es-encpos -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.http.ssl.enabled=false" elasticsearch:8.12.1
docker exec es-encpos bash -c "bin/elasticsearch-plugin install analysis-icu"
docker restart es-encpos
```

### Indexing
> :warning: Below (re)indexing commands are run within the app virtual environment:  
> reactivate the virtual environment if needed (`source venv/bin/activate`)  
> 
> In below commands, options are indicated within brackets <em>(option)</em>. Remove them as required.
> 
> With ES security enabled, the <em>ES_PASSWORD</em> option is required in commands below.

#### Initial indexing: 
```bash
(ES_PASSWORD={ELASTIC_PASSWORD}) python3 manage.py update-conf
(ES_PASSWORD={ELASTIC_PASSWORD}) python3 manage.py index (--years=YYYY-YYYY)
```

#### Update the indexes' configuration:
```bash
(ES_PASSWORD={ELASTIC_PASSWORD}) python3 manage.py update-conf --rebuild
```
The above command updates the indexes according to the project ES [configuration files](./elasticsearch/).  

#### Index or reindex (without index configuration changes):
```bash
(ES_PASSWORD={ELASTIC_PASSWORD}) python3 manage.py index (--years=YYYY-YYYY)
```

#### Check created indexes:
```bash
curl http://(elastic:{ELASTIC_PASSWORD}@)localhost:9200
```

## Launch the front-end:
- [Front-end's Readme](https://github.com/chartes/encpos-vue)

---
Additional details for offline commands:

```bash
python3 manage.py --help

Usage: manage.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands (need ES_PASSWORD with ES security enabled):
  delete       Delete the indexes
  index        Rebuild the elasticsearch indexes
  search       Perform a search using the provided query.
  update-conf  Update the index configuration and mappings

```
