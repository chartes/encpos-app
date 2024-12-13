# The [Position de Thèses](https://theses.chartes.psl.eu/) API
Elasticsearch API to search the ENC Thesis Abstracts ([Positions de thèses](https://theses.chartes.psl.eu/)).

![Static Badge](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&label=PYTHON&color=blue)

![Static Badge](https://img.shields.io/badge/Flask-3.1.0-blue?logo=flask)
![Static Badge](https://img.shields.io/badge/elasticsearch-8.12-blue?logo=elasticsearch)

## Prerequisite - Install Elasticsearch

### Install Elasticsearch _and_ its ICU plugin

:warning: Use an ES version compatible with [requirements.txt](./requirements.txt)
:information_source: Below commands are run independently/outside virtual environments (`deactivate`)
  - Elasticsearch: refer to your organisation instructions or [Elasticsearch guidelines](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html#elasticsearch-install-packages)
  - [ICU plugin](https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html): check if ICU is installed with `uconv -V`, otherwise:
    <pre><code><b><i>path/to/elasticsearch_folder</i></b>/bin/elasticsearch-plugin install analysis-icu</code></pre>

- With docker (security disabled)
    <pre><code>
      docker run --name <b><i>es-encpos</i></b> -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.http.ssl.enabled=false" elasticsearch:8.12.1
      docker exec <b><i>es-encpos</i></b> bash -c "bin/elasticsearch-plugin install analysis-icu"
      docker restart <b><i>es-encpos</i></b>
    </code></pre>



## Install

- Clone the GitHub repository in your projects' folder:
<pre>
<code>
  cd <b><i>path/to/projects_folder/</i></b>
  git clone https://github.com/chartes/encpos-app.git
</code>
</pre>
- Ensure you are running Python 3.12, for example with pyenv:
  ```bash
  pyenv shell 3.12
  ```

- Set up the virtual environment:
  <pre><code>
  cd <b><i>path/to/projects_folder</i></b>/encpos-app
  python -m venv <b><i>your_venv_name</i></b>
  source <b><i>your_venv_name</i></b>/bin/activate
  pip install -r requirements.txt
  </code></pre>

- For servers requiring uWSGI to run Python apps (remote Nginx servers):
  - check if uWSGI is installed `pip list --local`
  - install it in your virtual *__your_venv_name__* if it's not: `pip install uwsgi`.
  The WSGI application is located at `flask_app:flask_app`
  *NB : this command may require wheel:*
    - to check whether wheel is installed: `pip show wheel`
    - to install it if required: `pip install wheel`

## Indexing

- Install Elasticsearch and create indices _if they are not available_:

- Follow the ES installation & initial indexing instructions [above](#prerequisite---install-elasticsearch)

> :warning: Below (re)indexing commands are run within the app virtual environment:
> reactivate the virtual environment if needed (<code>source <b><i>your_venv_name</i></b>/bin/activate</code>)
>
> In below commands, options are indicated within brackets <em>(option)</em>. Remove them as required.
>
> With ES security enabled, the<em>ES_PASSWORD</em> option is required in commands below.

### Initial indexing (and reindexing without configuration changes):

<pre><code>
(ES_PASSWORD=<b><i>ELASTIC_PASSWORD</i></b>) python manage.py (--config=<b><i>local/staging/prod</i></b>) index --years <b><i>"YYYY-YYYY"</i></b>
</code></pre>

When the index doesn't exist it is created according to the project ES [configuration files](./elasticsearch/).

### Updating index configuration

This operation will delete the pre-existing index.

<pre><code>
(ES_PASSWORD=<b><i>ELASTIC_PASSWORD</i></b>) python manage.py (--config=<b><i>local/staging/prod</i></b>) update-conf --rebuild --indexes=<b><i>encpos_document/encpos_collection</i></b>
</code></pre>
The above command updates the indexes according to the project ES [configuration files](./elasticsearch/).

### Check created indexes:

- with ES security disabled:
<pre><code>
curl -X POST "http://localhost:9200/encpos_document/_refresh?pretty"
curl http://localhost:9200/_cat/indices?v
</code></pre>

- with ES security enabled:
<pre><code>
curl -X POST "http://elastic:<b><i>ELASTIC_PASSWORD</i></b>@localhost:9200/encpos_document/_refresh?pretty"
curl http://elastic:<b><i>ELASTIC_PASSWORD</i></b>@localhost:9200/_cat/indices?v
</code></pre>

## Launch the app:

> :warning: Below commands are mainly for local launch.
> For servers, apps may be started via processes management tools, refer to the servers documentation
  - Reactivate the virtual environment if needed (<code>source <b><i>your_venv_name</i></b>/bin/activate</code>)
  - Launch:
  from the subfolder containing flask_app.py (<code>cd <b><i>path/to/encpos_app</i></b></code>)
    <code>(ES_PASSWORD=<b><i>ELASTIC_PASSWORD</i></b>) python flask_app.py</code>
  - Then visit http://localhost:5003/api/1.0/search?query=content:Gaule to test it is running



## Launch the front-end:
- [Front-end's Readme](https://github.com/chartes/encpos-vue)

---
Additional details for offline commands:


```bash
python3 manage.py --help

Usage: manage.py [OPTIONS] COMMAND [ARGS]...

Options:
  --config [local|staging|prod]  select appropriate .env file to use
                                 [default: staging]
  --help                         Show this message and exit.

Commands:
  delete       Delete the indexes
  index        Rebuild the elasticsearch indexes
  search       Perform a search using the provided query.
  update-conf  Update the index configuration and mappings

```