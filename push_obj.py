import oci

# --- Configuration ---
# Load OCI config from the default location (~/.oci/config)
# Ensure your config file has the necessary credentials and region configured.
config = oci.config.from_file("config")

# Replace with your actual OCI Object Storage details
namespace = "ax4qsxvnsmtm"  # Found in OCI console under Object Storage
bucket_name = "mlops"  # Your target bucket name
object_name = "test1.txt"  # The name the object will have in the bucket
local_file_path = "test1.txt" # Path to the file you want to upload

# --- Initialize Object Storage Client ---
object_storage_client = oci.object_storage.ObjectStorageClient(config)

# --- Upload the Object ---
try:
    with open(local_file_path, "rb") as f:
        # put_object uploads the file content to the specified object in the bucket
        response = object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=f  # Pass the file object directly for efficient streaming
        )

    
    
    print("Object Storage Endpoint:", object_storage_client.base_client.endpoint)


    if response.status == 200:
        print(f"Successfully uploaded '{local_file_path}' to '{object_name}' in bucket '{bucket_name}'.")
    else:
        print(f"Failed to upload object. Status code: {response.status}")

except oci.exceptions.ServiceError as e:
    print(f"OCI Service Error: {e}")
except FileNotFoundError:
    print(f"Error: Local file '{local_file_path}' not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")