#! /bin/bash

echo "Chargement des variables d'environnement..."
source .env.prod
echo ".env chargé"

git clone https://${{ GH_TOKEN }}@github.com/${{ Projet-immo }}.git 

cd Projet-immo 
cp ../.env.prod .

docker stop immo-api
docker rm immo-api

docker build -t projet-immo:latest .

docker run -d -p ${PORT_API}:8000 --name immo-api projet-immo:latest

#echo ${ PORT_API }