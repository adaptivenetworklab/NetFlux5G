# Build Image
```
cd images/Open5Gs
docker build -t adaptive/open5gs:1.0 .
```

# Deployment Web-Manager & Mongo

```
docker compose -f webui-db.yaml up -d
```

# Deployment NGC and register subscribers

deploy the ngc core (open5gs) with:

```
docker compose -f ngc.yaml up -d
```

Register subscribers in ngc with `bash ./register_subscriber.sh`.


# Deploy gnodeb

gnb1.yaml is configured to deploy 1 gnodeb (gnb1) and 3 ues:

```
docker compose -f gnb1.yaml up -d
```

You can use gnb2.yaml to deploy a second gnodeb (gnb2) with 3 additional ues:

```
docker compose -f gnb2.yaml up -d
```


# Test

To test ue connectivity through RAN, first check which UE containers are running:

```
docker ps | grep ues
```

Then enter the appropriate UE container (e.g., gnb1-ues1):

```
docker compose -f gnb1.yaml exec ues1 /bin/bash
```

Check available tunnel interfaces:
```
ip link show | grep uesimtun
ip addr show uesimtun0
```

Test connectivity:
```
traceroute -i uesimtun0 google.com
ping -I uesimtun0 google.com
```

For comprehensive testing, you can also check:
```
# Check UE registration status
grep -i "registration\|attach" /var/log/ueransim/ue*.log

# Test data transfer between UEs
python3 -m http.server 8080 --bind $(ip addr show uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
```

ues container will have multiple interfaces (one for each ue). 
You can try each tunnel providing the flag '-i' in traceroute and '-I' in ping.

If you have deployed a second genodeb (gnb2) the command to enter in the ues container is:

```
docker compose -f gnb2.yaml exec ues2 /bin/bash
```


# Clean Up

Undeploy with:

```
docker compose -f gnb1.yaml down
docker compose -f gnb2.yaml down
docker compose -f ngc.yaml down -v

```
