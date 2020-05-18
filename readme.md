Usage:

Clone or download github repo \
Open IDE and move to "Project_AIR/" in terminal \
Run the service: \
docker-compose build \
docker-compose up \
Enter http://0.0.0.0:5001 in browser \
Choose expected genre from the list all "All genres", \
choose mp3 file, \
push "Search" button, \
receive the result

Building new index: \
docker exec -it projectair_flask_1 python index.py \
OR \
run index.py in IDE

Adding new file to index: \
Enter page http://0.0.0.0:5001/add

Demo video link: \
https://youtu.be/OHCogOeOkN8