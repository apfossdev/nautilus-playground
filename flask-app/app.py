from flask import Flask
import os
import psycopg2 
from kubernetes import client, config # here we import the necessary parts of k8s py client

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres-service") # here it looks for DB_HOST in the env of the k8s deployment, if DB_HOST is not present there then it defaults to the string postgres-service as DB_HOST, similarly with the next 3 lines below
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "super_duper_secret_postgres_password")
DB_NAME = os.getenv("POSTGRES_DB", "podtracker")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    return conn

# Below is the function to list all the pod names in the namespace, here -> new-beginnings
def list_pods():
  
    try:
        config.load_incluster_config() # while running inside k8s cluster use it's config
    except Exception as e:
        config.load_kube_config() # for local development/testing use local kube_config itself
    
    v1 = client.CoreV1Api() # we initialize k8s client api to interact with the pods, services and etc.
    pods = v1.list_namespaced_pod(namespace="new-beginnings") # calls k8s apis to get all the pods as objects in the namespace
    pod_names = [pod.metadata.name for pod in pods.items] # Loop through all the pod objects, get their individual names and store them in the pod_names array 
    return pod_names

@app.route("/")
def index():
    pod_names = list_pods() # call this function defined previously to get the list of pods
    
    conn = get_db_connection() # connect to postgreSQL
    cursor = conn.cursor()
    
    create_table_query = """
        CREATE TABLE IF NOT EXISTS pods (
            id SERIAL PRIMARY KEY,
            pod_name VARCHAR(255) NOT NULL
        );
    """
    cursor.execute(create_table_query)
    
    cursor.execute("TRUNCATE TABLE pods;")
    
    insert_query = "INSERT INTO pods (pod_name) VALUES (%s);"
    for name in pod_names:
        cursor.execute(insert_query, (name, ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return f"Stored pod names: {', '.join(pod_names)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
  
    

