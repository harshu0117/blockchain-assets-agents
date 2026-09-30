import urllib.request
import json
import os

doi = "doi:10.7910/DVN/HJZW8Q"
url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={doi}"

print(f"Querying Harvard Dataverse API for {doi}...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Status:", data.get("status"))
        dataset_version = data.get("data", {}).get("latestVersion", {})
        files = dataset_version.get("files", [])
        print(f"Total files found: {len(files)}")
        
        file_list = []
        for f in files:
            dataFile = f.get("dataFile", {})
            file_info = {
                "id": dataFile.get("id"),
                "filename": dataFile.get("filename"),
                "filesize": dataFile.get("filesize"),
                "contentType": dataFile.get("contentType"),
                "md5": dataFile.get("md5"),
                "download_url": f"https://dataverse.harvard.edu/api/access/datafile/{dataFile.get('id')}"
            }
            file_list.append(file_info)
            print(f"- {file_info['filename']} ({file_info['filesize']} bytes) -> ID: {file_info['id']}")
            
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        manifest_path = os.path.join(PROJECT_ROOT, "data", "dataverse_files.json")
        with open(manifest_path, "w") as out_f:
            json.dump(file_list, out_f, indent=2)
        print(f"Saved file metadata to {manifest_path} successfully.")

except Exception as e:
    print(f"Error accessing Dataverse API: {e}")
