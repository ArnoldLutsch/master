#Set permission on the kubectl command line
gcloud container clusters get-credentials dashboard-web --zone us-central1-a --project <YOUR-PROJECT>
# Create Pods in Kubernetes Cluster -f FILENAME
kubectl create -f DashboardPod.yaml