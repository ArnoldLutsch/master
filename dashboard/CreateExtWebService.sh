#Exposing an External IP Address to Access an Application in a Cluster
kubectl expose deployment dashboard-app --type=LoadBalancer --port 80 --target-port 8080