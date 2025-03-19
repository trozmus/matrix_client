import requests
from tqdm import tqdm
import json


class SynapseManager:
    def __init__(self, server_url, admin_token):
        self.server_url = server_url.rstrip("/")
        self.admin_token = admin_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }

    def remove_user(self, user_id):
        """Remove all users from a room before deletion."""
        url = f"{server_url}/_synapse/admin/v1/deactivate/{user_id}"

        data = {"erase": True}
        response = requests.post(url, json=data, headers=self.headers)
        print(response.text)
        return response.status_code == 200

    def get_all_testing_users(self):
        url = f"{server_url}/_synapse/admin/v2/users"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            users = response.json().get("users", [])
            filtered_users = [
                item for item in users if "user.00" in item["name"].lower()]
            return filtered_users
        else:
            print("Error fetching users:", response.text)


# Example usage
server_url = "https://connect.mudita.com"
admin_token = "syt_dHJvem11c2FkbQ_NkWWASSGtjCUUBrlHyFB_1pkHnZ"
synapse_manager = SynapseManager(server_url, admin_token)


users_delete_list = synapse_manager.get_all_testing_users()
for user in tqdm(users_delete_list):
    user_id = user["name"]
    ret = synapse_manager.remove_user(user_id)
    print(ret)
    # for room_id in tqdm(room_to_delete):
    #     # Delete a room by name
    #     # room_manager.delete_room_by_name_or_id("Room 1")

    #     # Delete a room by ID
    #     # print(room_id)
    #     room_manager.delete_room_by_name_or_id(room_id)
