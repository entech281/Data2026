# A sample data application

This application uses streamlit and motherduck

## TO RUN
### 1 Set up Python + virtual environment
Use your python ide to create python virtual environment

### 2 install requirements 
```commandline
pip install -r requirements.txt
```

### 3 set up Streamlit secrets file

The credentials needed to connect to motherduck and TBA must not be stored in files
   that are checked into git.
   
When the application runs in production, the secrets are set up
in streamlit console. When running locally, you
need to create diretory ".streamlit"
and put a file called secrets.toml in it. The file looks like this:

```text
[motherduck]
token='big long token an admin will give you'

```
### 4 run the streamlit app
```commandline
streamlit run Home.py
```
