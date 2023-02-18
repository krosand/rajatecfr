import docker
import tarfile
import os
import datetime
import json

# Chemin où sauvegarder les fichiers .tar des conteneurs
backup_path = "/mnt/backup/docker/"

# Initialisation du client Docker
client = docker.from_env()

# Récupération de la liste des conteneurs
containers = client.containers.list()

# Boucle sur chaque conteneur
for container in containers:
    # Nom du conteneur et de l'image
    name = container.name
    image = container.image

    # Nom du fichier de sauvegarde avec la date et l'heure actuelles
    backup_name = name + "-" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".tar"

    # Chemin où sauvegarder le fichier .tar
    backup_file = os.path.join(backup_path, backup_name)

    # Obtenir les informations sur les volumes montés et les réseaux utilisés
    volume_info = client.api.inspect_container(name)
    network_info = volume_info['NetworkSettings']

    # Ajouter les informations de réseau au fichier JSON de sauvegarde des volumes
    volume_info['NetworkSettings'] = network_info
    volume_file = os.path.join(backup_path, name + "-volumes.json")
    with open(volume_file, "w") as f:
        f.write(json.dumps(volume_info, indent=4))

    # Exporter le système de fichiers du conteneur dans un fichier tar
    with open(backup_file, "wb") as tar:
        tar_data, stat = container.get_archive("/")
        for chunk in tar_data:
            tar.write(chunk)

    # Sauvegarder l'image Docker
    image_backup_file = os.path.join(backup_path, image.tags[0].replace("/", "_") + ".tar")
    with open(image_backup_file, "wb") as f:
        for chunk in image.save():
            f.write(chunk)

    # Affichage du résultat de la sauvegarde
    print("Backup of container {} and image {} complete".format(name, image.tags[0]))
