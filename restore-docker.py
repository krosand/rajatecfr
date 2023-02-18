import docker
import tarfile
import os
import datetime
import json

# Chemin où se trouvent les fichiers de sauvegarde .tar des conteneurs
backup_path = "/mnt/backup/docker/"

# Initialisation du client Docker
client = docker.from_env()

# Récupération de la liste des fichiers de sauvegarde .tar dans le répertoire de sauvegarde
backup_files = os.listdir(backup_path)

# Boucle sur chaque fichier de sauvegarde
for backup_file in backup_files:
    # Vérifier s'il s'agit d'un fichier .tar
    if not backup_file.endswith(".tar"):
        continue

    # Nom du conteneur et de l'image à partir du nom de fichier de sauvegarde
    name = backup_file.split("-")[0]
    image_name = name.replace("_", "/")

    # Restaurer l'image Docker à partir du fichier .tar
    image_backup_file = os.path.join(backup_path, image_name + ".tar")
    with open(image_backup_file, "rb") as f:
        client.images.load(f.read())

    # Créer un nouveau conteneur à partir de l'image restaurée
    new_container = client.containers.create(image_name, name=name)

    # Charger les informations de montage et de réseau depuis le fichier JSON de sauvegarde des volumes
    volume_file = os.path.join(backup_path, name + "-volumes.json")
    with open(volume_file, "r") as f:
        volume_info = json.load(f)

    # Restaurer les informations de montage pour le nouveau conteneur
    for mount in volume_info['Mounts']:
        new_container.put_archive(mount['Destination'], tarfile.open(mount['Source'], 'r').extractall())

    # Restaurer les informations de réseau pour le nouveau conteneur
    if volume_info['NetworkSettings'] is not None:
        network_info = volume_info['NetworkSettings']['Networks']
        for network_name, network_data in network_info.items():
            client.networks.create(
                network_name,
                driver=network_data['Driver'],
                ipam=network_data['IPAMConfig'],
            )
        new_container.disconnect()
        for network_name, network_data in network_info.items():
            client.networks.get(network_name).connect(new_container, ipv4_address=network_data['IPAddress'])

    # Démarrer le nouveau conteneur
    new_container.start()

    # Affichage du résultat de la restauration
    print("Restoration of container {} and image {} complete".format(name, image_name))
